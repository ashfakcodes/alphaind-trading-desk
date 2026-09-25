import time
import base64
import json
import logging
import socket
import threading
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization

from app.config import settings

logger = logging.getLogger(__name__)

# Constants matching official @bitget-ai/bitget-agent-sdk v3.3.0
KEY_SIZE_BITS = 2048
KEY_SIZE_BYTES = KEY_SIZE_BITS // 8  # 256 bytes
SESSION_TTL_SEC = 300  # 5 minutes

DEFAULT_OAUTH_ENDPOINTS = {
    "authorizeBaseUrl": "https://www.bitget.com",
    "authorizePath": "/account/center/agent-subaccount-oauth",
    "apiBaseUrl": "https://www.bitget.com",
    "accountDataPath": "/v1/user/public/getAgentAccountData"
}


def _to_standard_base64(url_safe: str) -> str:
    """Converts a base64url string into standard base64 with correct padding."""
    padded = url_safe.replace("-", "+").replace("_", "/")
    remainder = len(padded) % 4
    if remainder:
        padded += "=" * (4 - remainder)
    return padded


def decrypt_rsa_split_codec(ciphertext_base64_url: str, private_key: rsa.RSAPrivateKey) -> str:
    """
    Decrypts multi-block RSA ciphertext according to Bitget's agentic split codec.
    Ciphertext is split into 256-byte blocks and decrypted using PKCS#1 v1.5 padding.
    """
    raw_b64 = _to_standard_base64(ciphertext_base64_url)
    ciphertext_bytes = base64.b64decode(raw_b64)

    if len(ciphertext_bytes) == 0 or len(ciphertext_bytes) % KEY_SIZE_BYTES != 0:
        raise ValueError(
            f"OAuth ciphertext has unexpected length ({len(ciphertext_bytes)} bytes). "
            f"Expected multiple of {KEY_SIZE_BYTES}."
        )

    chunks = []
    for offset in range(0, len(ciphertext_bytes), KEY_SIZE_BYTES):
        block = ciphertext_bytes[offset : offset + KEY_SIZE_BYTES]
        decrypted_block = private_key.decrypt(block, padding.PKCS1v15())
        chunks.append(decrypted_block)

    return b"".join(chunks).decode("utf-8")


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """
    Ephemeral HTTP handler that receives the browser redirect from Bitget.
    Extracts ?dataKey=... and serves a friendly browser completion page.
    """

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        data_key = qs.get("dataKey", [None])[0]

        session_id = getattr(self.server, "session_id", None)
        oauth_service = getattr(self.server, "oauth_service", None)

        if data_key and session_id and oauth_service:
            oauth_service.handle_callback(session_id, data_key)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="utf-8">
              <title>Alphaind · Bitget Authorization Complete</title>
              <style>
                body {
                  background: #070a0e;
                  color: #e2e8f0;
                  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  height: 100vh;
                  margin: 0;
                }
                .card {
                  background: rgba(14, 18, 25, 0.94);
                  border: 1px solid rgba(255, 255, 255, 0.12);
                  border-radius: 16px;
                  padding: 36px 32px;
                  text-align: center;
                  max-width: 440px;
                  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.08);
                }
                .icon-wrap {
                  width: 60px;
                  height: 60px;
                  border-radius: 50%;
                  background: rgba(25, 147, 248, 0.12);
                  border: 1px solid rgba(25, 147, 248, 0.3);
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  margin: 0 auto 20px auto;
                  box-shadow: 0 0 20px rgba(25, 147, 248, 0.25);
                }
                h1 { color: #f8fafc; font-size: 20px; font-weight: 700; margin: 0 0 10px 0; }
                p { color: #94a3b8; font-size: 13.5px; line-height: 1.5; margin: 0 0 22px 0; }
                .badge {
                  display: inline-flex;
                  align-items: center;
                  gap: 6px;
                  padding: 6px 14px;
                  background: rgba(25, 147, 248, 0.12);
                  border: 1px solid rgba(25, 147, 248, 0.3);
                  color: #60a5fa;
                  border-radius: 9999px;
                  font-size: 12px;
                  font-weight: 600;
                }
              </style>
            </head>
            <body>
              <div class="card">
                <div class="icon-wrap">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1993f8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76z"/>
                    <polyline points="9 12 11 14 15 10"/>
                  </svg>
                </div>
                <h1>Bitget Authorization Granted</h1>
                <p>Your Agentic Subaccount credentials have been securely transmitted to Alphaind.</p>
                <div class="badge">You can now close this window and return to Alphaind</div>
              </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Missing dataKey in OAuth callback.")


class BitgetOAuthService:
    """
    Manages Bitget Agentic Account OAuth sessions, ephemeral callback listeners,
    and RSA credential decryption.
    """

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._cleanup_timer: Optional[threading.Timer] = None
        self._schedule_cleanup()

    def _schedule_cleanup(self):
        """Periodically clean up expired OAuth sessions."""
        self._cleanup_expired_sessions()
        self._cleanup_timer = threading.Timer(60.0, self._schedule_cleanup)
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()

    def _cleanup_expired_sessions(self):
        now = time.time()
        with self._lock:
            expired = [sid for sid, s in self._sessions.items() if s["expires_at"] < now]
            for sid in expired:
                server = self._sessions[sid].get("server")
                if server:
                    try:
                        server.shutdown()
                    except Exception:
                        pass
                del self._sessions[sid]

    def _find_free_port(self) -> int:
        """Binds to port 0 on 127.0.0.1 to obtain an available ephemeral port."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    def start_oauth_session(self, host_ip: str = "127.0.0.1", base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Starts a new OAuth session:
        1. Generates ephemeral RSA 2048-bit keypair.
        2. Spawns an ephemeral HTTP callback listener on an unused port.
        3. Constructs the Bitget authorization URL.
        """
        session_id = f"bg_oauth_{int(time.time() * 1000)}_{threading.get_ident()}"

        # Generate RSA keypair
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=KEY_SIZE_BITS)
        public_key = private_key.public_key()

        # SPKI DER base64 public key (as expected by Bitget backend)
        pub_der = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        pub_base64 = base64.b64encode(pub_der).decode("utf-8")

        # Find available ephemeral port
        port = self._find_free_port()

        # Start ephemeral callback server
        server = HTTPServer(("127.0.0.1", port), OAuthCallbackHandler)
        setattr(server, "session_id", session_id)
        setattr(server, "oauth_service", self)

        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        # Build Bitget Authorize URL
        target_base = base_url or DEFAULT_OAUTH_ENDPOINTS["authorizeBaseUrl"]
        auth_path = DEFAULT_OAUTH_ENDPOINTS["authorizePath"]
        authorize_url = (
            f"{target_base}{auth_path}?"
            f"publicKey={pub_base64}&"
            f"clientServerIpAddress={host_ip}&"
            f"clientServerPort={port}"
        )

        now = time.time()
        session_data = {
            "session_id": session_id,
            "private_key": private_key,
            "public_key_b64": pub_base64,
            "port": port,
            "host_ip": host_ip,
            "server": server,
            "status": "pending",  # pending -> completed | failed | expired
            "created_at": now,
            "expires_at": now + SESSION_TTL_SEC,
            "credentials": None,
            "error": None
        }

        with self._lock:
            self._sessions[session_id] = session_data

        logger.info(f"[BitgetOAuth] Started session {session_id} on port {port}")
        return {
            "session_id": session_id,
            "authorize_url": authorize_url,
            "port": port,
            "host_ip": host_ip,
            "expires_in": SESSION_TTL_SEC
        }

    def handle_callback(self, session_id: str, data_key: str):
        """
        Called when the ephemeral server receives the callback from Bitget.
        Exchanges dataKey with Bitget public API and decrypts credentials.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                logger.warning(f"[BitgetOAuth] Callback received for unknown session: {session_id}")
                return

        # Perform account data fetch in background thread
        threading.Thread(target=self._exchange_and_decrypt, args=(session_id, data_key), daemon=True).start()

    def exchange_datakey_manually(self, session_id: str, data_key: str) -> Dict[str, Any]:
        """
        Allows manually or frontend-submitted dataKey to be exchanged directly.
        """
        return self._exchange_and_decrypt(session_id, data_key)

    def _exchange_and_decrypt(self, session_id: str, data_key: str) -> Dict[str, Any]:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise ValueError("OAuth session not found or expired.")
            private_key = session["private_key"]
            server = session.get("server")

        try:
            api_url = f"{DEFAULT_OAUTH_ENDPOINTS['apiBaseUrl']}{DEFAULT_OAUTH_ENDPOINTS['accountDataPath']}"
            resp = requests.post(
                api_url,
                json={"dataKey": data_key},
                headers={"Content-Type": "application/json", "User-Agent": "AlphaindDesk/1.0"},
                timeout=10.0
            )

            if not resp.ok:
                err_msg = f"Bitget account data request failed with HTTP {resp.status_code}: {resp.text}"
                logger.error(f"[BitgetOAuth] {err_msg}")
                with self._lock:
                    session["status"] = "failed"
                    session["error"] = err_msg
                return {"success": False, "error": err_msg}

            body = resp.json()
            if body.get("code") != "200" or not body.get("data"):
                err_msg = body.get("msg") or "Bitget response missing account data payload."
                logger.error(f"[BitgetOAuth] {err_msg}")
                with self._lock:
                    session["status"] = "failed"
                    session["error"] = err_msg
                return {"success": False, "error": err_msg}

            # Decrypt ciphertext
            ciphertext_base64_url = body["data"]
            decrypted_json_str = decrypt_rsa_split_codec(ciphertext_base64_url, private_key)
            account_data = json.loads(decrypted_json_str)

            credentials = {
                "userId": str(account_data.get("userId", "")),
                "apiKey": account_data.get("apiKey", ""),
                "secretKey": account_data.get("secretKey", ""),
                "passphrase": account_data.get("passphrase", ""),
                "accountType": "Bitget Agentic Subaccount",
                "obtainedAt": int(time.time() * 1000)
            }

            with self._lock:
                session["status"] = "completed"
                session["credentials"] = credentials
                session["error"] = None

            logger.info(f"[BitgetOAuth] Successfully exchanged and decrypted credentials for session {session_id}")
            return {"success": True, "credentials": credentials}

        except Exception as e:
            logger.error(f"[BitgetOAuth] Error exchanging dataKey: {e}", exc_info=True)
            with self._lock:
                session["status"] = "failed"
                session["error"] = str(e)
            return {"success": False, "error": str(e)}
        finally:
            if server:
                try:
                    server.shutdown()
                except Exception:
                    pass

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Queries status of an active session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return {"status": "expired", "error": "Session expired or not found"}

            if time.time() > session["expires_at"]:
                session["status"] = "expired"

            res = {
                "session_id": session_id,
                "status": session["status"],
                "created_at": session["created_at"],
                "expires_at": session["expires_at"],
                "error": session.get("error")
            }

            # If completed, return credentials so client can encrypt and store
            if session["status"] == "completed" and session.get("credentials"):
                res["credentials"] = session["credentials"]

            return res

    def simulate_mock_oauth_grant(self) -> Dict[str, Any]:
        """
        Generates a simulated Bitget Agentic OAuth response for testing / CI / hackathon evaluation.
        Uses valid RSA encryption/decryption roundtrip to verify cryptographic integrity.
        """
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=KEY_SIZE_BITS)
        public_key = private_key.public_key()

        mock_creds = {
            "userId": "bg_agent_982341",
            "apiKey": "bg_agent_live_9b4e18ac37",
            "secretKey": "bgs_8192a0e7192f4410a88b7762c9381f92aa718",
            "passphrase": "AlphaMindVault$2026",
            "accountType": "Bitget Agentic Subaccount (Simulated Live)",
            "obtainedAt": int(time.time() * 1000)
        }

        # Encrypt mock payload with RSA PKCS1v15 to test split codec
        payload_bytes = json.dumps(mock_creds).encode("utf-8")
        # Split into blocks of max 200 bytes for 2048-bit RSA PKCS1v15
        max_block = 200
        blocks = [payload_bytes[i:i + max_block] for i in range(0, len(payload_bytes), max_block)]
        encrypted_chunks = [public_key.encrypt(b, padding.PKCS1v15()) for b in blocks]
        full_ciphertext = b"".join(encrypted_chunks)
        ciphertext_b64url = base64.urlsafe_b64encode(full_ciphertext).decode("utf-8")

        # Decrypt using our standard function
        decrypted_str = decrypt_rsa_split_codec(ciphertext_b64url, private_key)
        recovered = json.loads(decrypted_str)

        return {
            "success": True,
            "mode": "simulation_grant",
            "credentials": recovered,
            "message": "Simulated Bitget Agentic OAuth handshake completed with verified RSA 2048-bit split-codec roundtrip."
        }


# Global singleton
bitget_oauth_service = BitgetOAuthService()
