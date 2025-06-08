#!/usr/bin/env python3
"""
Test script for savings account transfer restrictions.
This script tests the business rule that savings accounts can only transfer to user's own cheque accounts.
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"

def test_savings_restrictions():
    """Test savings account transfer restrictions"""
    print("=" * 60)
    print("TESTING SAVINGS ACCOUNT TRANSFER RESTRICTIONS")
    print("=" * 60)
    
    # Step 1: Register/Login user
    print("\n1. Registering/Login test user...")
    
    # Register user
    register_data = {
        "username": "testuser",
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "first_name": "Test",
        "last_name": "User"
    }
    
    register_response = requests.post(f"{BASE_URL}/register/", json=register_data)
    print(f"Registration status: {register_response.status_code}")
    if register_response.status_code not in [200, 201, 400]:
        print(f"Registration failed: {register_response.text}")
        return False
    
    # Login to get token
    login_data = {
        "username": "testuser",
        "password": TEST_PASSWORD
    }
    
    login_response = requests.post(f"{BASE_URL}/login/", json=login_data)
    print(f"Login status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return False
    
    token = login_response.json().get('access')
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"✓ Successfully logged in and got token")
    
    # Step 2: Get user's accounts
    print("\n2. Getting user's accounts...")
    
    accounts_response = requests.get(f"{BASE_URL}/accounts/", headers=headers)
    print(f"Accounts status: {accounts_response.status_code}")
    
    if accounts_response.status_code != 200:
        print(f"Failed to get accounts: {accounts_response.text}")
        return False
    
    accounts = accounts_response.json()
    print(f"Found {len(accounts)} accounts")
    
    savings_account = None
    cheque_account = None
    
    for account in accounts:
        print(f"  - Account {account['account_number']}: {account['account_type']} (Balance: ${account['balance']})")
        if account['account_type'] == 'saving':
            savings_account = account
        elif account['account_type'] == 'cheque':
            cheque_account = account
    
    if not savings_account:
        print("❌ No savings account found! Need to create one for testing.")
        return False
        
    if not cheque_account:
        print("❌ No cheque account found! Need to create one for testing.")
        return False
    
    print(f"✓ Found savings account: {savings_account['account_number']}")
    print(f"✓ Found cheque account: {cheque_account['account_number']}")
    
    # Step 3: Test valid transfer (savings to own cheque)
    print("\n3. Testing VALID transfer (savings to own cheque account)...")
    
    transfer_data = {
        "from_account_number": savings_account['account_number'],
        "to_account_number": cheque_account['account_number'],
        "amount": "10.00",
        "description": "Test transfer from savings to cheque"
    }
    
    transfer_response = requests.post(f"{BASE_URL}/transfer/", json=transfer_data, headers=headers)
    print(f"Transfer status: {transfer_response.status_code}")
    
    if transfer_response.status_code == 200:
        result = transfer_response.json()
        print(f"✓ VALID transfer successful!")
        print(f"  Transaction ID: {result.get('transaction_id')}")
        print(f"  New balance: ${result.get('new_balance')}")
    else:
        print(f"❌ VALID transfer failed: {transfer_response.text}")
        return False
    
    # Step 4: Test invalid transfer (savings to another user's account)
    print("\n4. Testing INVALID transfer (savings to another user's account)...")
    
    # We'll use a fake account number to simulate another user's account
    fake_account = "99999999"
    
    transfer_data = {
        "from_account_number": savings_account['account_number'],
        "to_account_number": fake_account,
        "amount": "5.00",
        "description": "Test invalid transfer"
    }
    
    transfer_response = requests.post(f"{BASE_URL}/transfer/", json=transfer_data, headers=headers)
    print(f"Transfer status: {transfer_response.status_code}")
    
    if transfer_response.status_code == 400 or transfer_response.status_code == 404:
        error_msg = transfer_response.json().get('error', 'Unknown error')
        print(f"✓ INVALID transfer correctly rejected: {error_msg}")
    else:
        print(f"❌ INVALID transfer should have been rejected but got: {transfer_response.text}")
        return False
    
    # Step 5: Register another user to test cross-user restriction
    print("\n5. Testing transfer to another user's account...")
    
    # Register second user
    register_data2 = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": TEST_PASSWORD,
        "first_name": "Test2",
        "last_name": "User2"
    }
    
    register_response2 = requests.post(f"{BASE_URL}/register/", json=register_data2)
    print(f"Second user registration status: {register_response2.status_code}")
    
    if register_response2.status_code in [200, 201]:
        # Login as second user to get their account
        login_response2 = requests.post(f"{BASE_URL}/login/", json={
            "username": "testuser2",
            "password": TEST_PASSWORD
        })
        
        if login_response2.status_code == 200:
            token2 = login_response2.json().get('access')
            headers2 = {"Authorization": f"Bearer {token2}"}
            
            # Get second user's accounts
            accounts_response2 = requests.get(f"{BASE_URL}/accounts/", headers=headers2)
            if accounts_response2.status_code == 200:
                accounts2 = accounts_response2.json()
                if accounts2:
                    other_user_account = accounts2[0]['account_number']
                    
                    # Try to transfer from savings to other user's account
                    transfer_data = {
                        "from_account_number": savings_account['account_number'],
                        "to_account_number": other_user_account,
                        "amount": "5.00",
                        "description": "Test cross-user transfer"
                    }
                    
                    transfer_response = requests.post(f"{BASE_URL}/transfer/", json=transfer_data, headers=headers)
                    print(f"Cross-user transfer status: {transfer_response.status_code}")
                    
                    if transfer_response.status_code == 400:
                        error_msg = transfer_response.json().get('error', 'Unknown error')
                        print(f"✓ Cross-user transfer correctly rejected: {error_msg}")
                    else:
                        print(f"❌ Cross-user transfer should have been rejected but got: {transfer_response.text}")
                        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL SAVINGS ACCOUNT RESTRICTION TESTS PASSED!")
    print("=" * 60)
    return True

def main():
    """Main function"""
    try:
        success = test_savings_restrictions()
        if success:
            print("\n🎉 All tests completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the Django server.")
        print("Make sure the Django development server is running on http://localhost:8000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
