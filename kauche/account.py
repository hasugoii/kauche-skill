"""Signed-in (non-anonymous) sessions for the KAUCHE internal API.

The app signs the Firebase user in with Google, LINE or phone, then sends that
user's Firebase ID token as `Authorization: Bearer`. Some endpoints
(e.g. ListProductsBySalesRanking, GetProduct, your own listings/orders) need such a
real user; anonymous tokens get `code 13`.

This module lets *you* (the account owner) establish that session without Claude ever
handling your password. You bring a credential you obtained yourself; the library
exchanges it for a Firebase ID token and persists the refresh token so the session
lasts. Supported credential sources:

- **refresh token** (universal): paste the Firebase refresh token from your own
  authenticated session once; we refresh it forever. `AccountSession.from_refresh_token`.
- **custom token**: a Firebase custom token (e.g. the `firebase_custom_token` returned by
  the LINE flow below). `AccountSession.from_custom_token`.
- **Google**: a Google OpenID `id_token` you got via Google sign-in.
  `AccountSession.from_google_id_token`.
- **LINE**: see `connect.KaucheAPI.line_login` for the two-step StartLineLogin /
  CompleteLineLogin flow that yields a custom token.

Phone auth (Firebase PhoneAuthProvider) needs reCAPTCHA/Play Integrity and is not
reproducible headlessly; use one of the above instead.

Firebase project: x-asia-kauche-prod. API key is the app's public client key (auth.py).
"""
from __future__ import annotations

import os
import time

from .auth import FIREBASE_API_KEY, _post

_IDENTITY = "https://identitytoolkit.googleapis.com/v1"
_SECURETOKEN = "https://securetoken.googleapis.com/v1"
_CACHE = os.environ.get("KAUCHE_ACCOUNT_CACHE",
                        os.path.join(os.path.expanduser("~"), ".cache", "kauche-api", "account.json"))

import json  # noqa: E402


class AccountSession:
    """A persistent non-anonymous Firebase session. Has `.id_token()` like the
    anonymous auth, so it drops straight into `KaucheAPI(auth=...)`."""

    def __init__(self, api_key: str = FIREBASE_API_KEY, cache_path: str = _CACHE):
        self.api_key = api_key
        self.cache_path = cache_path
        self._id_token = None
        self._refresh_token = None
        self._expires_at = 0.0
        self._load()

    # ---- persistence ----
    def _load(self):
        try:
            with open(self.cache_path, encoding="utf-8") as f:
                d = json.load(f)
            if d.get("api_key") == self.api_key:
                self._id_token = d.get("id_token")
                self._refresh_token = d.get("refresh_token")
                self._expires_at = d.get("expires_at", 0.0)
        except (OSError, ValueError):
            pass

    def _save(self):
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump({"api_key": self.api_key, "id_token": self._id_token,
                       "refresh_token": self._refresh_token, "expires_at": self._expires_at}, f)
        os.chmod(self.cache_path, 0o600)

    def _store(self, id_token, refresh_token, expires_in):
        self._id_token = id_token
        self._refresh_token = refresh_token
        self._expires_at = time.time() + int(expires_in) - 120
        self._save()

    def logged_in(self) -> bool:
        return bool(self._refresh_token)

    def logout(self):
        self._id_token = self._refresh_token = None
        self._expires_at = 0.0
        try:
            os.remove(self.cache_path)
        except OSError:
            pass

    # ---- establishing a session (constructors) ----
    @classmethod
    def from_refresh_token(cls, refresh_token: str, **kw) -> "AccountSession":
        s = cls(**kw)
        s._refresh_token = refresh_token
        s._expires_at = 0.0
        s.id_token()  # force a refresh now, persists
        return s

    @classmethod
    def from_custom_token(cls, custom_token: str, **kw) -> "AccountSession":
        s = cls(**kw)
        d = _post(f"{_IDENTITY}/accounts:signInWithCustomToken?key={s.api_key}",
                  {"token": custom_token, "returnSecureToken": True})
        s._store(d["idToken"], d["refreshToken"], d.get("expiresIn", "3600"))
        return s

    @classmethod
    def from_google_id_token(cls, google_id_token: str, **kw) -> "AccountSession":
        return cls._from_idp(google_id_token, "google.com", **kw)

    @classmethod
    def from_apple_id_token(cls, apple_id_token: str, **kw) -> "AccountSession":
        return cls._from_idp(apple_id_token, "apple.com", **kw)

    @classmethod
    def _from_idp(cls, id_token: str, provider_id: str, **kw) -> "AccountSession":
        s = cls(**kw)
        d = _post(f"{_IDENTITY}/accounts:signInWithIdp?key={s.api_key}", {
            "postBody": f"id_token={id_token}&providerId={provider_id}",
            "requestUri": "http://localhost", "returnSecureToken": True,
        })
        s._store(d["idToken"], d["refreshToken"], d.get("expiresIn", "3600"))
        return s

    # ---- token use ----
    def _refresh(self):
        d = _post(f"{_SECURETOKEN}/token?key={self.api_key}",
                  {"grant_type": "refresh_token", "refresh_token": self._refresh_token})
        self._store(d["id_token"], d.get("refresh_token", self._refresh_token), d.get("expires_in", "3600"))

    def id_token(self) -> str:
        if self._id_token and time.time() < self._expires_at:
            return self._id_token
        if not self._refresh_token:
            raise RuntimeError("Not logged in. Use AccountSession.from_* or `kauche login` first.")
        self._refresh()
        return self._id_token
