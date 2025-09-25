#!/usr/bin/env python3
"""
Simple test to verify basic functionality
"""

import sys
import os
import requests
import time

def test_server_health():
    """Test if server is running and healthy"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("✅ Server is healthy")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        return False
    except Exception as e:
        print(f"❌ Error checking server health: {e}")
        return False

def test_basic_endpoints():
    """Test basic API endpoints"""
    endpoints = [
        "/",
        "/health",
        "/docs"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint} is working")
            else:
                print(f"❌ {endpoint} returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing {endpoint}: {e}")

def main():
    """Run basic tests"""
    print("🧪 Running basic functionality tests...")
    
    # Wait a bit for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(5)
    
    # Test server health
    if not test_server_health():
        print("❌ Server health check failed")
        sys.exit(1)
    
    # Test basic endpoints
    test_basic_endpoints()
    
    print("🎉 Basic tests completed!")

if __name__ == "__main__":
    main()
