import httpx
import sys

BASE_URL = "http://localhost:8000/api/whatsapp"
VERIFY_TOKEN = "super_secret_whatsapp_verify_token_123"

def run_whatsapp_verification():
    print("Starting verification of WhatsApp Webhook endpoints...")

    # 1. Test GET Webhook Validation (Success)
    params_ok = {
        "hub.mode": "subscribe",
        "hub.verify_token": VERIFY_TOKEN,
        "hub.challenge": "123456789"
    }
    r = httpx.get(f"{BASE_URL}/webhook", params=params_ok)
    print(f"GET /webhook (Valid token): Status {r.status_code}, Response: '{r.text}'")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.text == "123456789", f"Expected '123456789', got '{r.text}'"

    # 2. Test GET Webhook Validation (Failure - Token Mismatch)
    params_fail = {
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong_token_xyz",
        "hub.challenge": "987654321"
    }
    r = httpx.get(f"{BASE_URL}/webhook", params=params_fail)
    print(f"GET /webhook (Invalid token): Status {r.status_code} (Expected: 403 Forbidden)")
    assert r.status_code == 403, f"Expected 403, got {r.status_code}"

    # 3. Test POST Webhook command processing
    # Helper to construct WhatsApp message webhook payload
    def make_whatsapp_payload(message_body: str, from_number: str = "1234567890") -> dict:
        return {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "1005229152402460",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "15556312490",
                                    "phone_number_id": "1150005601534512"
                                },
                                "messages": [
                                    {
                                        "from": from_number,
                                        "id": "wamid.HBgLMTIzNDU2Nzg5MFVBYh...",
                                        "timestamp": "1671234567",
                                        "text": {
                                            "body": message_body
                                        },
                                        "type": "text"
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }

    # Test "help" command
    print("\nSending 'help' command via WhatsApp webhook...")
    r = httpx.post(f"{BASE_URL}/webhook", json=make_whatsapp_payload("help"))
    print(f"POST /webhook ('help'): Status {r.status_code}, Response: {r.json()}")
    assert r.status_code == 200

    # Test "list" command
    print("\nSending 'list' command via WhatsApp webhook...")
    r = httpx.post(f"{BASE_URL}/webhook", json=make_whatsapp_payload("list"))
    print(f"POST /webhook ('list'): Status {r.status_code}, Response: {r.json()}")
    assert r.status_code == 200

    # Test "search Biotech" command
    print("\nSending 'search Biotech' command via WhatsApp webhook...")
    r = httpx.post(f"{BASE_URL}/webhook", json=make_whatsapp_payload("search Biotech"))
    print(f"POST /webhook ('search Biotech'): Status {r.status_code}, Response: {r.json()}")
    assert r.status_code == 200

    # Test "lead 1" command
    print("\nSending 'lead 1' command via WhatsApp webhook...")
    r = httpx.post(f"{BASE_URL}/webhook", json=make_whatsapp_payload("lead 1"))
    print(f"POST /webhook ('lead 1'): Status {r.status_code}, Response: {r.json()}")
    assert r.status_code == 200

    # Test fallback query "Hooli"
    print("\nSending fallback company name 'Hooli' via WhatsApp webhook...")
    r = httpx.post(f"{BASE_URL}/webhook", json=make_whatsapp_payload("Hooli"))
    print(f"POST /webhook ('Hooli'): Status {r.status_code}, Response: {r.json()}")
    assert r.status_code == 200

    # Test invalid command fallback
    print("\nSending invalid command via WhatsApp webhook...")
    r = httpx.post(f"{BASE_URL}/webhook", json=make_whatsapp_payload("xyz_unknown_command"))
    print(f"POST /webhook ('xyz_unknown_command'): Status {r.status_code}, Response: {r.json()}")
    assert r.status_code == 200

    print("\n🎉 ALL WHATSAPP WEBHOOK ENPOINTS VERIFIED SUCCESSFULY!")

if __name__ == "__main__":
    run_whatsapp_verification()
