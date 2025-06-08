#!/usr/bin/env python3
"""
Setup script to create test accounts for savings restriction testing.
This script creates a user with both cheque and savings accounts for testing.
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"

def setup_test_accounts():
    """Setup test accounts for restriction testing"""
    print("=" * 60)
    print("SETTING UP TEST ACCOUNTS")
    print("=" * 60)
    
    # Step 1: Register user
    print("\n1. Registering test user...")
    
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
    
    # Step 2: Login to get token
    print("\n2. Logging in...")
    
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
    
    print(f"✓ Successfully logged in")
    
    # Step 3: Create a cheque account
    print("\n3. Creating cheque account...")
    
    cheque_account_data = {
        "account_type": "cheque"
    }
    
    cheque_response = requests.post(f"{BASE_URL}/accounts/", json=cheque_account_data, headers=headers)
    print(f"Cheque account creation status: {cheque_response.status_code}")
    
    if cheque_response.status_code in [200, 201]:
        cheque_account = cheque_response.json()
        print(f"✓ Cheque account created: {cheque_account['account_number']}")
    else:
        print(f"❌ Failed to create cheque account: {cheque_response.text}")
        return False
    
    # Step 4: Create a savings account
    print("\n4. Creating savings account...")
    
    savings_account_data = {
        "account_type": "saving"
    }
    
    savings_response = requests.post(f"{BASE_URL}/accounts/", json=savings_account_data, headers=headers)
    print(f"Savings account creation status: {savings_response.status_code}")
    
    if savings_response.status_code in [200, 201]:
        savings_account = savings_response.json()
        print(f"✓ Savings account created: {savings_account['account_number']}")
    else:
        print(f"❌ Failed to create savings account: {savings_response.text}")
        return False
    
    # Step 5: Add some balance to savings account (simulate a deposit)
    print("\n5. Adding balance to savings account...")
    print("Note: In a real system, you would deposit money. For testing, we'll update via admin.")
    
    # Step 6: List all accounts
    print("\n6. Listing all accounts...")
    
    accounts_response = requests.get(f"{BASE_URL}/accounts/", headers=headers)
    if accounts_response.status_code == 200:
        accounts = accounts_response.json()
        print(f"Total accounts: {len(accounts)}")
        for account in accounts:
            print(f"  - {account['account_number']}: {account['account_type']} (Balance: ${account['balance']})")
    
    print("\n" + "=" * 60)
    print("✅ TEST ACCOUNTS SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Go to Django admin at http://localhost:8000/admin/")
    print("2. Add some balance to the savings account for testing")
    print("3. Run the savings restrictions test: python test_savings_restrictions.py")
    
    return True

def main():
    """Main function"""
    try:
        success = setup_test_accounts()
        if success:
            print("\n🎉 Setup completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Setup failed!")
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
