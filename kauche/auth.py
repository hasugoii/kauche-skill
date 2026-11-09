"""Anonymous Firebase authentication for the KAUCHE internal API.

KAUCHE's app API (api.kauche.com) authorizes requests with a Firebase ID token
(`Authorization: Bearer <idToken>`). The app lets you shop without signing up, so
it bootstraps an **anonymous** Firebase user. We reproduce that: Firebase Identity
Toolkit `accounts:signUp` with the app's public Firebase Web API key returns an
idToken for a throwaway anonymous user. No password, no personal account.

Verified 2026-11-09: anonymous token is accepted by api.kauche.com and App Check
is NOT enforced on the customer API. The API key below is a *client* identifier
embedded in the APK (not a secret); it only permits anonymous sign-in.

Tokens last ~1h; we cache the refresh token and mint fresh IDs as needed.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request

# From APK v2.164.0 resources (google-services): project x-asia-kauche-prod.
FIREBASE_API_KEY = os.environ.get("KAUCHE_FIREBASE_API_KEY", "AIzaSyCMT60jygkdhgCKGgoWHq6HiJP8ZVsx-6U")
_IDENTITY = "https://identitytoolkit.googleapis.com/v1"
_SECURETOKEN = "https://securetoken.googleapis.com/v1"
_CACHE = os.environ.get("KAUCHE_TOKEN_CACHE", os.path.join(os.path.expanduser("~"), ".cache", "kauche-api", "token.json"))


def _post(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json", "X-Android-Package": "com.kauche.kauche"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


class FirebaseAnonymousAuth:
    """Mints and refreshes an anonymous Firebase ID token, cached on disk."""

    def __init__(self, api_key: str = FIREBASE_API_KEY, cache_path: str = _CACHE):
        self.api_key = api_key
        self.cache_path = cache_path
        self._id_token = None
        self._refresh_token = None
        self._expires_at = 0.0
        self._load()

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
        try:
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump({
                    "api_key": self.api_key, "id_token": self._id_token,
                    "refresh_token": self._refresh_token, "expires_at": self._expires_at,
                }, f)
            os.chmod(self.cache_path, 0o600)
        except OSError:
            pass

    def _sign_up(self):
        d = _post(f"{_IDENTITY}/accounts:signUp?key={self.api_key}", {"returnSecureToken": True})
        self._id_token = d["idToken"]
        self._refresh_token = d["refreshToken"]
        self._expires_at = time.time() + int(d.get("expiresIn", "3600")) - 120
        self._save()

    def _refresh(self):
        d = _post(f"{_SECURETOKEN}/token?key={self.api_key}", {"grant_type": "refresh_token", "refresh_token": self._refresh_token})
        self._id_token = d["id_token"]
        self._refresh_token = d.get("refresh_token", self._refresh_token)
        self._expires_at = time.time() + int(d.get("expires_in", "3600")) - 120
        self._save()

    def id_token(self) -> str:
        """A valid anonymous ID token, reusing/refreshing/minting as needed."""
        if self._id_token and time.time() < self._expires_at:
            return self._id_token
        if self._refresh_token:
            try:
                self._refresh()
                return self._id_token
            except Exception:
                pass
        self._sign_up()
        return self._id_token
