#!/usr/bin/env python3
"""
Simple test script to verify the web server is working correctly.
Run this after starting bot.py to test the endpoints.
"""

import requests
import json
import sys

def test_health_check(base_url):
    """Test the health check endpoint"""
    print("=" * 60)
    print("Testing Health Check Endpoint (GET /)")
    print("=" * 60)
    
    try:
        response = requests.get(f"{base_url}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Health check passed!")
            return True
        else:
            print("❌ Health check failed!")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_trigger_endpoint(base_url):
    """Test the trigger endpoint"""
    print("\n" + "=" * 60)
    print("Testing Trigger Endpoint (GET /trigger)")
    print("=" * 60)
    print("⚠️  This will attempt to create an Oracle Cloud instance!")
    print("⚠️  Make sure your OCI credentials are configured correctly.")

    confirm = input("\nProceed with trigger test? (y/n): ")
    if confirm.lower() != 'y':
        print("Skipping trigger test.")
        return None

    try:
        print("\nSending GET request to /trigger...")
        response = requests.get(f"{base_url}/trigger", timeout=180)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        result = response.json()
        status = result.get("status")
        
        if status == "success":
            print("✅ Instance created successfully!")
            return True
        elif status == "out_of_capacity":
            print("⚠️  Out of capacity (expected - will retry on next trigger)")
            return True
        elif status == "error":
            print("❌ Configuration error - check your OCI credentials")
            return False
        else:
            print("❌ Unexpected response")
            return False
    except requests.exceptions.Timeout:
        print("⚠️  Request timed out (instance creation can take 60+ seconds)")
        print("Check server logs for actual result")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("Oracle Cloud Bot - Web Server Test")
    print("=" * 60)
    
    # Get base URL
    base_url = input("\nEnter base URL (default: http://localhost:10000): ").strip()
    if not base_url:
        base_url = "http://localhost:10000"
    
    # Remove trailing slash
    base_url = base_url.rstrip('/')
    
    print(f"\nTesting server at: {base_url}")
    
    # Test health check
    health_ok = test_health_check(base_url)
    
    if not health_ok:
        print("\n❌ Health check failed. Make sure the server is running.")
        print("Start the server with: python bot.py")
        sys.exit(1)
    
    # Test trigger endpoint
    test_trigger_endpoint(base_url)
    
    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Deploy to Render (see QUICK_START.md)")
    print("2. Set up cron job to hit /trigger every 10 minutes")
    print("3. Monitor logs for instance creation attempts")
    print("\n")

if __name__ == "__main__":
    main()

