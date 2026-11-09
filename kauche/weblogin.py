"""Browser login for KAUCHE, MCP-style: open a link, sign in, token comes back.

`run_web_login()` starts a tiny local web server on 127.0.0.1, opens a page in your
browser that signs you into KAUCHE's Firebase project with Google or Apple (Firebase JS
`signInWithPopup`), and captures the resulting Firebase idToken + refreshToken back into
an AccountSession. No password ever reaches Claude or this process — the OAuth happens
between your browser and Google/Apple + Firebase.

Why it works headlessly: `http://localhost` is a default authorized domain on every
Firebase project, and KAUCHE's Google provider is enabled, so the standard Firebase web
sign-in runs from the local page. LINE is a custom provider (no Firebase popup) — use the
LINE flow in connect.py / `references/internal-api.md` instead.

If your browser shows `auth/unauthorized-domain` (the project removed localhost), fall
back to `kauche login --refresh-token <...>` / `--google-id-token <...>`.
"""
from __future__ import annotations

import http.server
import json
import threading
import urllib.parse
import webbrowser

from .account import AccountSession

# Firebase web config (from APK v2.164.0 google-services; apiKey is a public client key).
FIREBASE_WEB_CONFIG = {
    "apiKey": "AIzaSyCMT60jygkdhgCKGgoWHq6HiJP8ZVsx-6U",
    "authDomain": "x-asia-kauche-prod.firebaseapp.com",
    "projectId": "x-asia-kauche-prod",
    "storageBucket": "x-asia-kauche-prod.appspot.com",
    "messagingSenderId": "283378856219",
    "appId": "1:283378856219:android:b75fd1b919e81735ab23be",
}

_PAGE = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>KAUCHE login</title>
<style>body{font-family:system-ui,sans-serif;max-width:420px;margin:60px auto;padding:0 16px;color:#222}
button{font-size:16px;padding:12px 18px;margin:8px 0;width:100%;border:1px solid #ccc;border-radius:10px;background:#fff;cursor:pointer}
button:hover{background:#f5f5f5}#msg{margin-top:16px;white-space:pre-wrap}</style></head>
<body><h2>KAUCHE login</h2><p>Sign in to issue a token for the CLI. Nothing is sent to anyone but Google/Apple and Firebase.</p>
<button id="google">Sign in with Google</button>
<button id="apple">Sign in with Apple</button>
<div id="msg"></div>
<script type="module">
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth, GoogleAuthProvider, OAuthProvider, signInWithPopup } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
const cfg = __CONFIG__;
const app = initializeApp(cfg); const auth = getAuth(app); auth.useDeviceLanguage();
const msg = document.getElementById("msg");
async function go(provider){
  msg.textContent = "Opening sign-in popup...";
  try{
    const cred = await signInWithPopup(auth, provider);
    const idToken = await cred.user.getIdToken(true);
    const refreshToken = cred.user.refreshToken;
    const r = await fetch("/token", {method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({idToken, refreshToken, email: cred.user.email||"", uid: cred.user.uid})});
    msg.textContent = r.ok ? "Signed in. You can close this tab and return to the terminal."
                           : "Captured token but the CLI did not accept it; check the terminal.";
  }catch(e){ msg.textContent = "Error: " + (e&&e.code||e) + "\\n" +
    "If it says auth/unauthorized-domain, use `kauche login --refresh-token` instead."; }
}
document.getElementById("google").onclick = () => { const p=new GoogleAuthProvider(); p.setCustomParameters({prompt:"select_account"}); go(p); };
document.getElementById("apple").onclick = () => go(new OAuthProvider("apple.com"));
</script></body></html>"""


class WebLogin:
    """A running local login server. Non-blocking: start() returns a URL immediately;
    the token is captured in the background and persisted to an AccountSession. Good for
    MCP (one tool returns the link, another checks status)."""

    def __init__(self, port: int = 0):
        self._result = {}
        self.done = threading.Event()
        self.session = None
        page = _PAGE.replace("__CONFIG__", json.dumps(FIREBASE_WEB_CONFIG))
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                if urllib.parse.urlparse(self.path).path in ("/", "/index.html"):
                    body = page.encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_POST(self):
                if urllib.parse.urlparse(self.path).path != "/token":
                    self.send_response(404)
                    self.end_headers()
                    return
                n = int(self.headers.get("Content-Length", 0))
                try:
                    data = json.loads(self.rfile.read(n).decode())
                except ValueError:
                    data = {}
                ok = bool(data.get("idToken") and data.get("refreshToken"))
                self.send_response(200 if ok else 400)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                if ok:
                    outer._result.update(data)
                    try:
                        outer.session = AccountSession.from_tokens(
                            data["idToken"], data["refreshToken"], email=data.get("email") or None)
                    finally:
                        outer.done.set()

        self._srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self.url = f"http://127.0.0.1:{self._srv.server_address[1]}/"

    def start(self, open_browser: bool = True) -> str:
        threading.Thread(target=self._srv.serve_forever, daemon=True).start()
        if open_browser:
            try:
                webbrowser.open(self.url)
            except Exception:
                pass
        return self.url

    def wait(self, timeout: int = 300) -> AccountSession:
        got = self.done.wait(timeout)
        self._srv.shutdown()
        if not got:
            raise TimeoutError("web login timed out; no token received")
        return self.session

    def stop(self):
        try:
            self._srv.shutdown()
        except Exception:
            pass


def run_web_login(port: int = 0, timeout: int = 300, open_browser: bool = True) -> AccountSession:
    wl = WebLogin(port)
    print(f"Open this link to sign in (also opening it in your browser):\n  {wl.url}")
    wl.start(open_browser=open_browser)
    return wl.wait(timeout)
