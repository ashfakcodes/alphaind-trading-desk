import pytest
import json
import base64
import time
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from run import app
from app.services.bitget_oauth import (
    bitget_oauth_service,
    decrypt_rsa_split_codec,
    KEY_SIZE_BITS,
    KEY_SIZE_BYTES
)
from app.services.bitget_client import bitget_client

client = TestClient(app)

# -------------------------------------------------------------
# 1. Cryptographic RSA Keypair & Split-Codec Tests
# -------------------------------------------------------------

def test_rsa_keypair_and_split_codec_roundtrip():
    """Verify that multi-block payload is cleanly encrypted and decrypted via RSA split codec."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=KEY_SIZE_BITS)
    public_key = private_key.public_key()

    payload = {
        "userId": "bg_agent_test_4821",
        "apiKey": "bg_live_key_a8723491bc90",
        "secretKey": "bg_secret_ff82194a081bc7723910abec128741",
        "passphrase": "AlphaMindVault$Secure2026",
        "accountType": "Bitget Agentic Subaccount"
    }
    payload_bytes = json.dumps(payload).encode("utf-8")

    # Split into 200-byte blocks and encrypt each with PKCS1v15
    block_size = 200
    blocks = [payload_bytes[i:i + block_size] for i in range(0, len(payload_bytes), block_size)]
    encrypted_chunks = [public_key.encrypt(b, padding.PKCS1v15()) for b in blocks]
    ciphertext = b"".join(encrypted_chunks)
    ciphertext_b64url = base64.urlsafe_b64encode(ciphertext).decode("utf-8")

    # Decrypt via Bitget split codec
    decrypted_str = decrypt_rsa_split_codec(ciphertext_b64url, private_key)
    recovered = json.loads(decrypted_str)

    assert recovered["userId"] == payload["userId"]
    assert recovered["apiKey"] == payload["apiKey"]
    assert recovered["secretKey"] == payload["secretKey"]
    assert recovered["passphrase"] == payload["passphrase"]


def test_decrypt_invalid_ciphertext_length():
    """Invalid ciphertext length that is not a multiple of 256 bytes must raise ValueError."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=KEY_SIZE_BITS)
    invalid_bytes = b"short_invalid_bytes"
    invalid_b64url = base64.urlsafe_b64encode(invalid_bytes).decode("utf-8")

    with pytest.raises(ValueError) as exc:
        decrypt_rsa_split_codec(invalid_b64url, private_key)
    assert "unexpected length" in str(exc.value).lower()


# -------------------------------------------------------------
# 2. Bitget OAuth Service Lifecycle Tests
# -------------------------------------------------------------

def test_oauth_service_start_session():
    """Verify session creation, ephemeral port allocation, and Bitget authorize_url."""
    session = bitget_oauth_service.start_oauth_session(host_ip="127.0.0.1")

    assert "session_id" in session
    assert session["session_id"].startswith("bg_oauth_")
    assert session["port"] > 1024
    assert "publicKey=" in session["authorize_url"]
    assert "clientServerIpAddress=127.0.0.1" in session["authorize_url"]
    assert f"clientServerPort={session['port']}" in session["authorize_url"]

    # Verify session is registered as pending
    status = bitget_oauth_service.get_session_status(session["session_id"])
    assert status["status"] == "pending"


def test_oauth_service_simulate_grant():
    """Verify mock OAuth grant produces valid credentials with verified roundtrip."""
    sim = bitget_oauth_service.simulate_mock_oauth_grant()
    assert sim["success"] is True
    assert "credentials" in sim
    assert sim["credentials"]["userId"].startswith("bg_agent_")
    assert sim["credentials"]["apiKey"].startswith("bg_agent_live_")
    assert "secretKey" in sim["credentials"]
    assert "passphrase" in sim["credentials"]


# -------------------------------------------------------------
# 3. Bitget Client Dynamic Credentials Tests
# -------------------------------------------------------------

def test_bitget_client_credential_management():
    """Verify runtime credential swapping and reverting."""
    # Snapshot original
    orig_key = bitget_client.api_key
    orig_sim = bitget_client.is_simulation

    try:
        # Set agentic subaccount credentials
        bitget_client.set_credentials(
            api_key="bg_test_agent_123456",
            api_secret="secret_abc",
            passphrase="pass_xyz",
            is_simulation=False,
            user_id="uid_agent_99",
            account_type="Bitget Agentic Subaccount"
        )

        auth_info = bitget_client.get_auth_info()
        assert auth_info["authenticated"] is True
        assert auth_info["is_simulation"] is False
        assert auth_info["user_id"] == "uid_agent_99"
        assert auth_info["masked_key"] == "bg_tes...3456"

        # Revert credentials
        bitget_client.clear_credentials()
        reverted_info = bitget_client.get_auth_info()
        assert reverted_info["user_id"] == ""
        assert reverted_info["account_type"] == "Bitget Simulation / Default"

    finally:
        bitget_client.api_key = orig_key
        bitget_client.is_simulation = orig_sim


# -------------------------------------------------------------
# 4. FastAPI OAuth Endpoints Integration Tests
# -------------------------------------------------------------

def test_api_oauth_start():
    resp = client.post("/api/oauth/start", json={"host_ip": "127.0.0.1"})
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert "authorize_url" in data
    assert "port" in data


def test_api_oauth_simulate_and_sync():
    # 1. Simulate grant
    sim_resp = client.post("/api/oauth/simulate")
    assert sim_resp.status_code == 200
    sim_data = sim_resp.json()
    creds = sim_data["credentials"]

    # 2. Sync to desk
    sync_resp = client.post("/api/oauth/sync", json={
        "api_key": creds["apiKey"],
        "secret_key": creds["secretKey"],
        "passphrase": creds["passphrase"],
        "user_id": creds["userId"],
        "is_simulation": False
    })
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()
    assert sync_data["status"] == "synchronized"
    assert sync_data["auth"]["user_id"] == creds["userId"]

    # 3. Check status endpoint
    status_resp = client.get("/api/oauth/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["auth"]["authenticated"] is True
    assert status_data["desk_mode"] == "Bitget Agentic Live Subaccount"

    # 4. Disconnect
    disc_resp = client.post("/api/oauth/disconnect")
    assert disc_resp.status_code == 200
    disc_data = disc_resp.json()
    assert disc_data["status"] == "disconnected"


def test_api_oauth_sync_camel_case_direct():
    """Verify frontend direct camelCase credentials payload syncs properly without manual translation."""
    creds = {
        "userId": "9836952706",
        "apiKey": "bg_agent_live_9b4e18ac37",
        "secretKey": "bgs_8192a0e7192f4410a88b7762c9381f92aa718",
        "passphrase": "AlphaMindVault$2026",
        "accountType": "Bitget Agentic Subaccount",
        "isSimulation": False
    }
    sync_resp = client.post("/api/oauth/sync", json=creds)
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()
    assert sync_data["status"] == "synchronized"
    assert sync_data["auth"]["user_id"] == "9836952706"
    assert sync_data["auth"]["authenticated"] is True
    assert "balances" in sync_data
    assert "USDT" in sync_data["balances"]

    # Verify /api/account/status reports the authenticated state and live balances
    acc_resp = client.get("/api/account/status")
    assert acc_resp.status_code == 200
    acc_data = acc_resp.json()
    assert acc_data["auth_info"]["authenticated"] is True
    assert acc_data["auth_info"]["user_id"] == "9836952706"
    assert "USDT" in acc_data["balances"]

    # Clean up
    client.post("/api/oauth/disconnect")


def test_bitget_client_v3_list_response_handling(monkeypatch):
    """Verify that get_account_balances correctly parses the standard Bitget v3 array of assets."""
    bitget_client.set_credentials(
        api_key="mock_key",
        api_secret="mock_secret",
        passphrase="mock_pass",
        is_simulation=False,
        user_id="9836952706"
    )

    # Mock requests session get to return a Bitget v3 list payload for assets and empty for funding
    def mock_get(url, *args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                if "/api/v3/account/assets" in url:
                    return {
                        "code": "00000",
                        "msg": "success",
                        "data": [
                            {"coin": "USDT", "available": "2450.50", "balance": "2450.50"},
                            {"coin": "BTC", "available": "0.12", "balance": "0.12"}
                        ]
                    }
                return {"code": "00000", "msg": "success", "data": []}
        return MockResponse()

    monkeypatch.setattr(bitget_client.session, "get", mock_get)

    try:
        balances = bitget_client.get_account_balances()
        assert balances["USDT"] == 2450.50
        assert balances["BTC"] == 0.12
    finally:
        bitget_client.clear_credentials()

