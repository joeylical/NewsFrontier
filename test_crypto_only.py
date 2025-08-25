#!/usr/bin/env python3
"""
Standalone test script for crypto functionality only.

This script tests just the encryption/decryption capabilities without database dependencies.
"""

import os
import sys
import logging
from pathlib import Path

# Add lib to Python path
lib_path = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_path))

# Set a test master key for testing
os.environ["CRYPTO_MASTER_KEY"] = "test_master_key_12345_for_testing"

def test_crypto_directly():
    """Test crypto module directly without other dependencies."""
    print("🔐 Testing crypto module directly...")
    
    try:
        # Import only the crypto module
        from newsfrontier_lib.crypto import KeyManager, generate_master_key, test_encryption
        
        # Test key generation
        print("  🔑 Testing key generation...")
        master_key = generate_master_key()
        if len(master_key) >= 32:
            print(f"    ✅ Generated master key: {master_key[:10]}...{master_key[-10:]}")
        else:
            print(f"    ❌ Key too short: {len(master_key)} characters")
            return False
        
        # Test KeyManager initialization
        print("  🔧 Testing KeyManager initialization...")
        key_manager = KeyManager()
        if key_manager.is_available():
            print("    ✅ KeyManager initialized successfully")
        else:
            print("    ❌ KeyManager not available")
            return False
        
        # Test string encryption/decryption
        print("  🔒 Testing string encryption...")
        test_string = "sk-test-api-key-12345-secret"
        encrypted = key_manager.encrypt(test_string)
        
        if not encrypted:
            print("    ❌ Failed to encrypt test string")
            return False
        
        print(f"    🔒 Encrypted: {encrypted[:50]}...")
        
        decrypted = key_manager.decrypt(encrypted)
        if decrypted != test_string:
            print(f"    ❌ Decryption mismatch: expected '{test_string}', got '{decrypted}'")
            return False
        
        print(f"    🔓 Decrypted: {decrypted}")
        
        # Test dictionary encryption/decryption
        print("  📝 Testing dictionary encryption...")
        test_dict = {
            "api_key": "sk-test-key-123",
            "endpoint": "https://api.example.com",
            "model": "gpt-4"
        }
        
        encrypted_dict = key_manager.encrypt_dict(test_dict)
        if not encrypted_dict:
            print("    ❌ Failed to encrypt dictionary")
            return False
        
        print(f"    🔒 Encrypted dict: {encrypted_dict[:50]}...")
        
        decrypted_dict = key_manager.decrypt_dict(encrypted_dict)
        if decrypted_dict != test_dict:
            print(f"    ❌ Dict decryption mismatch: expected {test_dict}, got {decrypted_dict}")
            return False
        
        print(f"    🔓 Decrypted dict: {decrypted_dict}")
        
        # Test the built-in test function
        print("  🧪 Testing built-in test function...")
        if test_encryption():
            print("    ✅ Built-in test passed")
        else:
            print("    ❌ Built-in test failed")
            return False
        
        print("  ✅ All crypto tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Crypto test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n🎯 Testing edge cases...")
    
    try:
        from newsfrontier_lib.crypto import KeyManager
        
        key_manager = KeyManager()
        
        # Test empty string
        encrypted = key_manager.encrypt("")
        if encrypted is None:
            print("    ✅ Empty string returns None")
        else:
            print("    ❌ Empty string should return None")
            return False
        
        # Test None value
        encrypted = key_manager.encrypt(None)
        if encrypted is None:
            print("    ✅ None value returns None")
        else:
            print("    ❌ None value should return None")
            return False
        
        # Test invalid encrypted data
        decrypted = key_manager.decrypt("invalid_encrypted_data")
        if decrypted is None:
            print("    ✅ Invalid encrypted data returns None")
        else:
            print("    ❌ Invalid encrypted data should return None")
            return False
        
        # Test large string
        large_string = "A" * 10000
        encrypted = key_manager.encrypt(large_string)
        if encrypted:
            decrypted = key_manager.decrypt(encrypted)
            if decrypted == large_string:
                print("    ✅ Large string encryption/decryption works")
            else:
                print("    ❌ Large string decryption failed")
                return False
        else:
            print("    ❌ Large string encryption failed")
            return False
        
        print("  ✅ All edge case tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Edge case test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_different_master_keys():
    """Test that different master keys produce different results."""
    print("\n🔑 Testing different master keys...")
    
    try:
        from newsfrontier_lib.crypto import KeyManager
        
        # Test with first key
        os.environ["CRYPTO_MASTER_KEY"] = "first_test_key_12345"
        key_manager1 = KeyManager()
        
        # Test with second key
        os.environ["CRYPTO_MASTER_KEY"] = "second_test_key_67890"
        key_manager2 = KeyManager()
        
        test_string = "test-api-key-123"
        
        # Encrypt with first key
        encrypted1 = key_manager1.encrypt(test_string)
        # Encrypt with second key
        encrypted2 = key_manager2.encrypt(test_string)
        
        if encrypted1 != encrypted2:
            print("    ✅ Different master keys produce different encrypted results")
        else:
            print("    ❌ Different master keys produced same encrypted result")
            return False
        
        # Test that each can only decrypt its own
        decrypted1_with1 = key_manager1.decrypt(encrypted1)
        decrypted2_with2 = key_manager2.decrypt(encrypted2)
        decrypted1_with2 = key_manager2.decrypt(encrypted1)
        decrypted2_with1 = key_manager1.decrypt(encrypted2)
        
        if (decrypted1_with1 == test_string and 
            decrypted2_with2 == test_string and
            decrypted1_with2 is None and
            decrypted2_with1 is None):
            print("    ✅ Keys can only decrypt their own encrypted data")
        else:
            print("    ❌ Cross-key decryption behavior incorrect")
            return False
        
        # Restore original test key
        os.environ["CRYPTO_MASTER_KEY"] = "test_master_key_12345_for_testing"
        
        print("  ✅ Master key isolation tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Master key test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all crypto-specific tests."""
    print("🧪 NewsFrontier Crypto Module Test Suite")
    print("=" * 50)
    
    # Set up logging to suppress verbose output
    logging.getLogger().setLevel(logging.WARNING)
    
    tests = [
        ("Basic Crypto Functions", test_crypto_directly),
        ("Edge Cases", test_edge_cases),
        ("Master Key Isolation", test_different_master_keys),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"  ✅ {test_name} PASSED")
            else:
                print(f"  ❌ {test_name} FAILED")
        except Exception as e:
            print(f"  💥 {test_name} CRASHED: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All crypto tests passed! Encryption functionality is working correctly.")
        print("\n💡 Next steps:")
        print("   1. Set CRYPTO_MASTER_KEY in your .env file")
        print("   2. Install enhanced dependencies: pip install -r requirements-enhanced.txt")
        print("   3. Run database migrations to set up configuration tables")
        return 0
    else:
        print("⚠️  Some crypto tests failed. Please check the cryptography installation.")
        return 1


if __name__ == "__main__":
    exit(main())