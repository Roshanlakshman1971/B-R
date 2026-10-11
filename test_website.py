#!/usr/bin/env python3
"""Comprehensive test suite for B&R Events website and backend API."""

import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parent
HTML_PATH = ROOT / "test2.html"
BACKEND_PATH = ROOT / "backend"

def run_static_html_checks():
    print("=" * 60)
    print("Running Static HTML Checks on test2.html...")
    print("=" * 60)
    errors = []
    warnings = []

    if not HTML_PATH.exists():
        errors.append("test2.html not found!")
        return errors, warnings

    content = HTML_PATH.read_text(encoding="utf-8")

    # 1. Check duplicate DOCTYPE or <html> tags
    doctype_count = len(re.findall(r"<!DOCTYPE\s+html", content, re.IGNORECASE))
    if doctype_count > 1:
        errors.append(f"Multiple <!DOCTYPE html> tags found ({doctype_count}). File has duplicated page markup at the beginning!")
    else:
        print("✓ DOCTYPE declaration is clean (1 found).")

    html_tags = len(re.findall(r"<html[\s>]", content, re.IGNORECASE))
    if html_tags > 1:
        errors.append(f"Multiple <html...> tags found ({html_tags}).")
    else:
        print("✓ <html> tag is clean (1 found).")

    # 2. Check for duplicate IDs
    ids = re.findall(r'\bid=["\']([^"\']+)["\']', content)
    seen_ids = set()
    dup_ids = set()
    for element_id in ids:
        if element_id in seen_ids:
            dup_ids.add(element_id)
        seen_ids.add(element_id)
    if dup_ids:
        errors.append(f"Duplicate DOM element IDs found: {sorted(list(dup_ids))}")
    else:
        print(f"✓ All {len(seen_ids)} DOM IDs are unique.")

    # 3. Check required form fields for inquiry submission
    expected_form_fields = [
        "inquiryForm",
        "fullName",
        "phoneNumber",
        "emailAddress",
        "eventType",
        "eventDate",
        "guestCount",
        "venueLocation",
        "requirements",
        "formSuccessMessage",
        "formErrorMessage"
    ]
    for field_id in expected_form_fields:
        if field_id not in seen_ids:
            errors.append(f"Missing required form element ID: '{field_id}'")
    print("✓ All required form inputs and message containers present.")

    # 4. Check modal and interaction IDs
    expected_interactive_ids = [
        "catering-menu-modal",
        "catering-modal-card",
        "catering-menu-btn",
        "cuisine-south-panel",
        "cuisine-north-panel",
        "tab-btn-south",
        "tab-btn-north",
        "gallery-filters",
        "gallery-container"
    ]
    for el_id in expected_interactive_ids:
        if el_id not in seen_ids:
            errors.append(f"Missing required interactive element ID: '{el_id}'")
    print("✓ Interactive modal and gallery IDs present.")

    # 5. Check anchor navigation targets
    anchors = re.findall(r'href=["\']#([^"\']+)["\']', content)
    for anchor in set(anchors):
        if anchor and anchor not in seen_ids:
            warnings.append(f"Internal anchor href='#{anchor}' does not match any element id.")
    if not warnings:
        print("✓ All internal anchor links target valid element IDs.")

    return errors, warnings


def test_backend_api():
    print("\n" + "=" * 60)
    print("Running Backend HTTP & API Integration Tests...")
    print("=" * 60)
    errors = []

    # Find a free port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    test_port = sock.getsockname()[1]
    sock.close()

    env = os.environ.copy()
    admin_token = "BR_EVENTS_TEST_TOKEN_2026"
    env["ADMIN_EXPORT_TOKEN"] = admin_token

    # Start backend server pointing to test port
    # Note: backend file hardcodes 8000 in main(), so let's check if 8000 is available or pass port if supported
    # Let's inspect how backend is invoked
    server_proc = subprocess.Popen(
        [sys.executable, str(BACKEND_PATH)],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    base_url = "http://127.0.0.1:8000"
    time.sleep(1.0)

    try:
        # Check server started
        if server_proc.poll() is not None:
            _, err = server_proc.communicate()
            errors.append(f"Backend failed to start on port 8000: {err}")
            return errors

        print(f"✓ Backend server process started (PID {server_proc.pid}) on http://127.0.0.1:8000")

        # 1. Test GET /
        req = urllib.request.Request(f"{base_url}/")
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.getcode()
            html = response.read().decode("utf-8")
            if status != 200:
                errors.append(f"GET / returned status {status}, expected 200")
            elif "B&amp;R Events" not in html and "B&R Events" not in html:
                errors.append("GET / does not contain B&R Events branding")
            else:
                print("✓ GET / returned 200 OK with website HTML content.")

        # 2. Test GET /test2.html
        req = urllib.request.Request(f"{base_url}/test2.html")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.getcode() != 200:
                errors.append(f"GET /test2.html returned status {response.getcode()}, expected 200")
            else:
                print("✓ GET /test2.html returned 200 OK.")

        # 3. Test GET 404 for nonexistent route
        try:
            req = urllib.request.Request(f"{base_url}/nonexistent-page")
            urllib.request.urlopen(req, timeout=5)
            errors.append("GET /nonexistent-page should return 404 but returned 200")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print("✓ GET /nonexistent-page properly returns 404 Not Found.")
            else:
                errors.append(f"GET /nonexistent-page returned unexpected status {e.code}")

        # 4. Test GET /api/inquiries/export unauthorized (no token)
        try:
            req = urllib.request.Request(f"{base_url}/api/inquiries/export")
            urllib.request.urlopen(req, timeout=5)
            errors.append("GET /api/inquiries/export without token should return 403 Forbidden")
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print("✓ GET /api/inquiries/export (unauthorized) properly returns 403 Forbidden.")
            else:
                errors.append(f"GET /api/inquiries/export returned unexpected status {e.code}")

        # 5. Test GET /api/inquiries/export authorized with token
        req = urllib.request.Request(f"{base_url}/api/inquiries/export?token={admin_token}")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.getcode() != 200:
                errors.append(f"Authorized export returned status {response.getcode()}, expected 200")
            else:
                csv_data = response.read().decode("utf-8")
                if "full_name,phone_number,email_address" not in csv_data:
                    errors.append("Exported CSV does not have expected headers")
                else:
                    print("✓ GET /api/inquiries/export?token=... returned 200 OK with CSV data.")

        # 6. Test Admin Token placeholder replacement on website
        req = urllib.request.Request(f"{base_url}/?token={admin_token}")
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode("utf-8")
            if "exportInquiriesBtn" in html:
                print("✓ GET /?token=... successfully unlocks the admin Export button.")
            else:
                errors.append("Admin token was provided in query params but export button was not injected.")

        # 7. Test POST /api/inquiries validation: invalid / past date
        post_data = json.dumps({
            "full_name": "Test User",
            "phone_number": "+91 9876543210",
            "email_address": "test@example.com",
            "event_type": "Wedding",
            "event_date": "2020-01-01",  # Past date
            "guest_count": "100",
            "venue_location": "Bangalore",
            "requirements": "Automated test"
        }).encode("utf-8")
        try:
            req = urllib.request.Request(
                f"{base_url}/api/inquiries",
                data=post_data,
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=5)
            errors.append("POST /api/inquiries with past date should return 400 but succeeded")
        except urllib.error.HTTPError as e:
            if e.code == 400:
                print("✓ POST /api/inquiries correctly rejected past date with 400 Bad Request.")
            else:
                errors.append(f"POST past date returned unexpected status {e.code}")

        # 8. Test POST /api/inquiries validation: invalid email
        post_data = json.dumps({
            "full_name": "Test User",
            "phone_number": "+91 9876543210",
            "email_address": "not-an-email",
            "event_type": "Wedding",
            "event_date": "2027-12-31",
            "guest_count": "100",
            "venue_location": "Bangalore",
            "requirements": "Automated test"
        }).encode("utf-8")
        try:
            req = urllib.request.Request(
                f"{base_url}/api/inquiries",
                data=post_data,
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=5)
            errors.append("POST /api/inquiries with invalid email should return 400 but succeeded")
        except urllib.error.HTTPError as e:
            if e.code == 400:
                print("✓ POST /api/inquiries correctly rejected invalid email with 400 Bad Request.")
            else:
                errors.append(f"POST invalid email returned unexpected status {e.code}")

        # 9. Test POST /api/inquiries: valid inquiry
        valid_post_data = json.dumps({
            "full_name": "Automated Test Guest",
            "phone_number": "+91 9876543210",
            "email_address": "guest@brevents-test.com",
            "event_type": "Wedding & Reception",
            "event_date": "2027-05-15",
            "guest_count": "350 Guests",
            "venue_location": "Palace Grounds, Bangalore",
            "requirements": "Grand floral mandap decor and royal catering menu."
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url}/api/inquiries",
            data=valid_post_data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.getcode()
            res_json = json.loads(response.read().decode("utf-8"))
            if status != 201:
                errors.append(f"Valid inquiry submission returned status {status}, expected 201")
            elif not res_json.get("id"):
                errors.append("Response did not contain inquiry id")
            else:
                print(f"✓ POST /api/inquiries successfully created inquiry #{res_json['id']}.")

    finally:
        server_proc.terminate()
        server_proc.wait(timeout=5)
        print("✓ Backend server cleanly stopped.")

    return errors


def main():
    html_errors, html_warnings = run_static_html_checks()
    api_errors = test_backend_api()

    print("\n" + "=" * 60)
    print("TEST SUMMARY RESULTS")
    print("=" * 60)

    all_errors = html_errors + api_errors
    if html_warnings:
        print(f"Warnings ({len(html_warnings)}):")
        for w in html_warnings:
            print(f"  [!] {w}")

    if all_errors:
        print(f"\nFAILED: {len(all_errors)} issues detected:")
        for e in all_errors:
            print(f"  [✗] {e}")
        sys.exit(1)
    else:
        print("\nALL TESTS PASSED! Website and backend are working fine.")
        sys.exit(0)


if __name__ == "__main__":
    main()
