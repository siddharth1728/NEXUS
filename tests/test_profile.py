def test_get_profile(client, csrf_token):
    # Register & Login first
    client.post(
        "/api/auth/register",
        json={"email": "profile@example.com", "password": "securepassword123"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "profile@example.com", "password": "securepassword123"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    
    access_cookie = login_resp.cookies.get("access_token")
    
    # Get Profile
    resp = client.get("/api/profile", cookies={"access_token": access_cookie})
    assert resp.status_code == 200
    data = resp.json()
    assert data["target_role_id"] is None
    
    # Update Profile
    update_resp = client.put(
        "/api/profile",
        json={"github_username": "nexus_student"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token, "access_token": access_cookie}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["github_username"] == "nexus_student"
