import urllib.request
import json

def test_api():
    # 1. Login
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/auth/login",
        data=json.dumps({"email": "admin@campaignportal.io", "password": "test"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    token = json.loads(res.read())["access_token"]
    print(f"✅ Login successful, token: {token[:10]}...")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 2. Add real contact
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/contacts",
        data=json.dumps({
            "email": "test-recipient@example.com",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+15551234567"
        }).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    res = urllib.request.urlopen(req)
    contact = json.loads(res.read())
    print(f"✅ Contact created: {contact['email']}")

    # 3. Create Campaign
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/campaigns",
        data=json.dumps({
            "name": "Integration Test Campaign",
            "channel": "email",
            "message_template": "Hello {{first_name}}, this is a real test.",
            "target_audience": "test-recipient@example.com"
        }).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    res = urllib.request.urlopen(req)
    campaign = json.loads(res.read())
    camp_id = campaign['id']
    print(f"✅ Campaign created: {camp_id}")

    # 4. Start Campaign
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/campaigns/{camp_id}/start",
        headers=headers,
        method="POST"
    )
    res = urllib.request.urlopen(req)
    print(f"✅ Campaign started")

    # 5. Dispatch Campaign
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/campaigns/{camp_id}/send",
        headers=headers,
        method="POST"
    )
    res = urllib.request.urlopen(req)
    dispatch = json.loads(res.read())
    print(f"✅ Campaign dispatched: {dispatch['messages_sent']} sent")

    print("\n🎉 ALL TESTS PASSED!")

if __name__ == "__main__":
    test_api()
