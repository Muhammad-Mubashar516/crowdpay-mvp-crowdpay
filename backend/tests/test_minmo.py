#!/usr/bin/env python3
"""
Test script for Minmo API integration
Run this to verify your Minmo setup is working correctly
"""

import os
import sys
from dotenv import load_dotenv

# Add the parent directory to path so we can import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.minmo import create_minmo_swap, verify_minmo_signature, get_minmo_exchange_rates

def test_env_setup():
    """Test that all required environment variables are set"""
    print(" Testing environment setup...")
    
    load_dotenv()
    required_vars = ['MINMO_API_KEY', 'MINMO_WEBHOOK_SECRET']
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f" {var}: {'*' * len(value[:4])}...")  # Show first 4 chars
        else:
            print(f" {var}: Not set")
    
    print()

def test_signature_verification():
    """Test webhook signature verification"""
    print("Testing signature verification...")
    
    # Test with mock data
    test_payload = b'{"id":"test123","status":"completed"}'
    test_signature = "invalid_signature"
    
    result = verify_minmo_signature(test_payload, test_signature)
    print(f"Signature verification function working: {not result}")  # Should return False for invalid sig
    print()

def test_exchange_rates():
    """Test fetching exchange rates (requires valid API key)"""
    print("Testing exchange rates...")
    
    try:
        rates = get_minmo_exchange_rates()
        print(f"Exchange rates fetched successfully")
        print(f"   Available rates: {list(rates.keys()) if isinstance(rates, dict) else 'Unknown format'}")
    except Exception as e:
        print(f"Failed to fetch exchange rates: {e}")
    
    print()

def test_swap_creation():
    """Test creating a swap (will fail without valid API key and webhook URL)"""
    print("Testing swap creation...")
    
    try:
        # This will likely fail in testing, but we can check the error handling
        swap = create_minmo_swap(
            amount_kes=1000.0,
            callback_url="https://yourdomain.com/api/webhooks/minmo",
            metadata={"test": "true"},
            payment_method="mpesa"
        )
        print(f"Swap created successfully: {swap.get('id', 'unknown')}")
    except Exception as e:
        print(f"Swap creation failed (expected in test): {e}")
        print("   This is normal if API key is not configured or webhook URL is invalid")
    
    print()

if __name__ == "__main__":
    print("Minmo API Integration Test\n")
    
    test_env_setup()
    test_signature_verification()
    test_exchange_rates()
    test_swap_creation()
    
    print("Test completed!")
    print("\nNext steps:")
    print("1. Set up your .env file with valid MINMO_API_KEY and MINMO_WEBHOOK_SECRET")
    print("2. Update MINMO_BASE_URL if necessary")
    print("3. Test with real API credentials")
