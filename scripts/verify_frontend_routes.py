import httpx
import sys

BASE_URL = "http://localhost:8000"

def test_frontend_rendering():
    print("Starting verification of frontend rendering endpoints...")
    
    # 1. Test root dashboard GET
    try:
        r = httpx.get(f"{BASE_URL}/")
        print(f"GET /: Status {r.status_code}")
        assert r.status_code == 200, f"Expected status 200, got {r.status_code}"
        assert "<!DOCTYPE html>" in r.text, "Expected HTML doctype template in response"
        assert "Sales Intelligence Dashboard" in r.text, "Expected dashboard title inside HTML body"
        print("✅ HTML Dashboard serves successfully at '/' root.")
    except Exception as e:
        print(f"Failed to load frontend root: {e}")
        sys.exit(1)

    # 2. Test docs dashboard GET
    try:
        r = httpx.get(f"{BASE_URL}/docs")
        print(f"GET /docs: Status {r.status_code}")
        assert r.status_code == 200, f"Expected status 200, got {r.status_code}"
        assert "<!DOCTYPE html>" in r.text, "Expected HTML doctype template in response"
        assert "Platform System Architecture" in r.text, "Expected documentation title inside HTML body"
        print("✅ HTML Documentation serves successfully at '/docs'.")
    except Exception as e:
        print(f"Failed to load docs root: {e}")
        sys.exit(1)

    # 3. Test static assets loading
    try:
        r_css = httpx.get(f"{BASE_URL}/static/styles.css")
        print(f"GET /static/styles.css: Status {r_css.status_code}")
        assert r_css.status_code == 200, f"Expected 200, got {r_css.status_code}"
        assert "--bg-main" in r_css.text, "Expected variables in stylesheet"
        print("✅ Static CSS serves successfully.")
        
        r_js = httpx.get(f"{BASE_URL}/static/app.js")
        print(f"GET /static/app.js: Status {r_js.status_code}")
        assert r_js.status_code == 200, f"Expected 200, got {r_js.status_code}"
        print("✅ Static JavaScript serves successfully.")
    except Exception as e:
        print(f"Failed to load static assets: {e}")
        sys.exit(1)

    print("\n🎉 ALL FRONTEND ROUTING HAS BEEN VERIFIED AND OPERATIONAL!")

if __name__ == "__main__":
    test_frontend_rendering()
