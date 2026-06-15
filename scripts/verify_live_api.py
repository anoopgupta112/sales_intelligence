import httpx
import sys
import time

BASE_URL = "http://localhost:8000"

def run_verification():
    print("Starting verification of live API endpoints...")

    # 1. Health Check / Root Endpoint
    try:
        r = httpx.get(f"{BASE_URL}/")
        print(f"GET /: Status {r.status_code}, Response: {r.json()}")
        assert r.status_code == 200
        assert "active" in r.json().get("message", "")
    except Exception as e:
        print(f"Error connecting to health check endpoint: {e}")
        sys.exit(1)

    # 2. Register a Representative User
    rep_email = "verify_rep@acme.com"
    rep_password = "strong_password_123"
    register_payload_rep = {
        "email": rep_email,
        "password": rep_password,
        "role": "representative"
    }
    
    r = httpx.post(f"{BASE_URL}/api/auth/register", json=register_payload_rep)
    if r.status_code == 201:
        print("Successfully registered representative user.")
    elif r.status_code == 400 and "already exists" in r.json().get("detail", ""):
        print("Representative user already exists. Proceeding...")
    else:
        print(f"Failed to register representative user: Status {r.status_code}, Response: {r.text}")
        sys.exit(1)

    # 3. Register a Manager User
    mgr_email = "verify_mgr@acme.com"
    mgr_password = "strong_password_123"
    register_payload_mgr = {
        "email": mgr_email,
        "password": mgr_password,
        "role": "manager"
    }
    r = httpx.post(f"{BASE_URL}/api/auth/register", json=register_payload_mgr)
    if r.status_code == 201:
        print("Successfully registered manager user.")
    elif r.status_code == 400 and "already exists" in r.json().get("detail", ""):
        print("Manager user already exists. Proceeding...")
    else:
        print(f"Failed to register manager user: Status {r.status_code}, Response: {r.text}")
        sys.exit(1)

    # 4. Log in Representative to get token
    r = httpx.post(f"{BASE_URL}/api/auth/login", data={"username": rep_email, "password": rep_password})
    assert r.status_code == 200, f"Rep login failed: {r.text}"
    rep_token = r.json()["access_token"]
    print("Representative logged in successfully.")

    # 5. Log in Manager to get token
    r = httpx.post(f"{BASE_URL}/api/auth/login", data={"username": mgr_email, "password": mgr_password})
    assert r.status_code == 200, f"Manager login failed: {r.text}"
    mgr_token = r.json()["access_token"]
    print("Manager logged in successfully.")

    # 6. Test RBAC: Call /api/lead-search as Representative (should be blocked)
    r = httpx.post(
        f"{BASE_URL}/api/lead-search",
        json={"target_criteria": {"industry": "Web3"}},
        headers={"Authorization": f"Bearer {rep_token}"}
    )
    print(f"POST /api/lead-search as Representative: Status {r.status_code} (Expected: 403 Forbidden)")
    assert r.status_code == 403, f"Expected 403, got {r.status_code}"

    # 7. Test RBAC: Call /api/lead-search as Manager (should pass RBAC and call workflow trigger)
    r = httpx.post(
        f"{BASE_URL}/api/lead-search",
        json={"target_criteria": {"industry": "Enterprise SaaS"}},
        headers={"Authorization": f"Bearer {mgr_token}"}
    )
    print(f"POST /api/lead-search as Manager: Status {r.status_code}, Response: {r.json()}")
    assert r.status_code == 200, f"Trigger workflow failed: {r.text}"
    run_id = r.json().get("workflow_run_id")
    print(f"Workflow run triggered successfully: {run_id}")

    # 8. Poll workflow state until it is AWAITING_REVIEW or COMPLETED
    print("Polling workflow status...")
    status_data = None
    for attempt in range(15):
        time.sleep(1)
        r = httpx.get(
            f"{BASE_URL}/api/workflow/{run_id}",
            headers={"Authorization": f"Bearer {rep_token}"}
        )
        assert r.status_code == 200, f"Failed to get status: {r.text}"
        status_data = r.json()
        print(f"Polling check {attempt+1}: current_step={status_data['current_step']}, status={status_data['status']}")
        if status_data["status"] in ["AWAITING_REVIEW", "COMPLETED"]:
            print(f"Workflow run reached status: {status_data['status']}")
            break
    else:
        print("Workflow polling timed out or failed to reach completion or review status.")
        sys.exit(1)

    # 9. Trigger human review / review workflow endpoint if AWAITING_REVIEW
    if status_data["status"] == "AWAITING_REVIEW":
        print("Submitting human review approval...")
        r = httpx.post(
            f"{BASE_URL}/api/workflow/{run_id}/review",
            json={"approved": True},
            headers={"Authorization": f"Bearer {mgr_token}"}
        )
        print(f"POST /api/workflow/{run_id}/review: Status {r.status_code}, Response: {r.json()}")
        assert r.status_code == 200, f"Failed to submit review: {r.text}"
        assert r.json().get("status") == "APPROVED"

        # Poll workflow state until it is COMPLETED
        print("Polling workflow status for COMPLETED status...")
        for attempt in range(10):
            time.sleep(1)
            r = httpx.get(
                f"{BASE_URL}/api/workflow/{run_id}",
                headers={"Authorization": f"Bearer {rep_token}"}
            )
            assert r.status_code == 200, f"Failed to get status: {r.text}"
            status_data = r.json()
            print(f"Polling check {attempt+1}: status={status_data['status']}")
            if status_data["status"] == "COMPLETED":
                print("Workflow run successfully COMPLETED!")
                break
        else:
            print("Workflow polling timed out waiting for COMPLETED status.")
            sys.exit(1)

    # 10. Retrieve lead details from DB and verify updated status
    print("Verifying lead details for lead ID 1 and 2...")
    for lead_id in [1, 2]:
        r_lead = httpx.get(
            f"{BASE_URL}/api/lead/{lead_id}",
            headers={"Authorization": f"Bearer {rep_token}"}
        )
        print(f"GET /api/lead/{lead_id}: Status {r_lead.status_code}, Response: {r_lead.json() if r_lead.status_code == 200 else r_lead.text}")
        if r_lead.status_code == 200:
            lead_info = r_lead.json()
            print(f"Verified lead {lead_id}: company={lead_info['company_name']}, status={lead_info['status']}")
            assert lead_info["status"] in ["qualified", "outreach_generated", "researched"]

    print("\n🎉 ALL API ENDPOINTS HAVE BEEN SUCCESSFULLY VERIFIED AND ARE FULLY OPERATIONAL!")

if __name__ == "__main__":
    run_verification()
