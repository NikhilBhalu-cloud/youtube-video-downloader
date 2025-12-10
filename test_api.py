#!/usr/bin/env python
"""Test script for API endpoints"""
import requests
import json

BASE_URL = "http://localhost:5000"

# Test with a short, public YouTube video
TEST_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - 18 seconds

def test_qualities():
    """Test getting video qualities"""
    print(f"\n🔍 Testing /api/qualities endpoint...")
    print(f"   URL: {TEST_URL}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/qualities", json={"url": TEST_URL}, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success!")
            print(f"   Title: {data.get('title')}")
            print(f"   Available formats: {len(data.get('formats', []))}")
            
            # Find and print high quality formats
            for fmt in data.get('formats', [])[:3]:  # First 3 formats
                print(f"      - {fmt.get('resolution')} ({fmt.get('filesize_mb')} MB) [{fmt.get('format_id')}]")
            
            return data
        else:
            print(f"   ❌ Error: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("API Endpoint Tester")
    print("=" * 60)
    
    test_qualities()
