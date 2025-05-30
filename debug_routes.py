#!/usr/bin/env python3

import requests
import json

BASE_URL = "http://localhost:8095"

def test_routes():
    print("Testing route functionality...")
    
    # Test 1: GET /api/prompts/prompts/nara_admin (should work - catch-all route)
    print("\n1. Testing GET /api/prompts/prompts/nara_admin")
    response = requests.get(f"{BASE_URL}/api/prompts/prompts/nara_admin")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✓ GET route works")
    else:
        print(f"✗ GET route failed: {response.text[:100]}")
    
    # Test 2: PUT /api/prompts/prompts/nara_admin (should work - specific route)
    print("\n2. Testing PUT /api/prompts/prompts/nara_admin")
    data = {"content": "test content"}
    response = requests.put(f"{BASE_URL}/api/prompts/prompts/nara_admin", 
                           json=data, 
                           headers={"Content-Type": "application/json"})
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✓ PUT route works")
    else:
        print(f"✗ PUT route failed: {response.text[:100]}")
    
    # Test 3: GET /api/prompts/prompts/nara_admin/referenced_by (should work - specific route)
    print("\n3. Testing GET /api/prompts/prompts/nara_admin/referenced_by")
    response = requests.get(f"{BASE_URL}/api/prompts/prompts/nara_admin/referenced_by")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✓ Referenced_by route works")
        print(f"Response: {response.text}")
    else:
        print(f"✗ Referenced_by route failed: {response.text[:100]}")

if __name__ == "__main__":
    test_routes()
