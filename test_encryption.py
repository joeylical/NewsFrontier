#!/usr/bin/env python3
"""
Test script for encryption functionality.

This script tests the encryption/decryption capabilities and configuration service.
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

def test_basic_encryption():
    """Test basic encryption and decryption."""
    print("🔐 Testing basic encryption...")
    
    try:
        from newsfrontier_lib.crypto import get_key_manager, test_encryption
        
        # Test the built-in test function
        if test_encryption():
            print("  ✅ Built-in encryption test passed")
        else:
            print("  ❌ Built-in encryption test failed")
            return False
        
        # Test manual encryption/decryption
        key_manager = get_key_manager()
        
        if not key_manager.is_available():
            print("  ❌ Key manager not available")
            return False
        
        # Test string encryption
        test_string = "sk-test-api-key-12345-secret"
        encrypted = key_manager.encrypt(test_string)
        
        if not encrypted:
            print("  ❌ Failed to encrypt test string")
            return False
        
        print(f"  🔒 Encrypted: {encrypted[:50]}...")
        
        decrypted = key_manager.decrypt(encrypted)
        
        if decrypted != test_string:
            print(f"  ❌ Decryption mismatch: expected '{test_string}', got '{decrypted}'")
            return False
        
        print(f"  🔓 Decrypted: {decrypted}")
        print("  ✅ Manual encryption test passed")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Encryption test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration_service():
    """Test configuration service functionality."""
    print("\n⚙️  Testing configuration service...")
    
    try:
        from newsfrontier_lib.config_service import get_config, ConfigKeys
        from newsfrontier_lib.init_config import init_default_settings
        
        config = get_config()
        
        # Test setting a plain value
        success = config.set("test_setting", "test_value", "string", "Test setting")
        if success:
            print("  ✅ Successfully set plain configuration value")
        else:
            print("  ❌ Failed to set plain configuration value")
            return False
        
        # Test getting a plain value
        value = config.get("test_setting")
        if value == "test_value":
            print(f"  ✅ Successfully retrieved plain value: {value}")
        else:
            print(f"  ❌ Retrieved wrong value: expected 'test_value', got '{value}'")
            return False
        
        # Test setting an encrypted value
        api_key = "sk-test-encrypted-api-key-67890"
        success = config.set_encrypted("test_api_key", api_key, "Test API key")
        if success:
            print("  ✅ Successfully set encrypted configuration value")
        else:
            print("  ❌ Failed to set encrypted configuration value")
            return False
        
        # Test getting an encrypted value
        decrypted_key = config.get_encrypted("test_api_key")
        if decrypted_key == api_key:
            print(f"  ✅ Successfully retrieved encrypted value: {decrypted_key}")
        else:
            print(f"  ❌ Decrypted value mismatch: expected '{api_key}', got '{decrypted_key}'")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enhanced_clients():
    """Test enhanced client initialization."""
    print("\n🚀 Testing enhanced clients...")
    
    try:
        from newsfrontier_lib.llm_client_new import get_enhanced_llm_client
        from newsfrontier_lib.s3_client_new import get_enhanced_s3_client
        
        # Test enhanced LLM client
        llm_client = get_enhanced_llm_client()
        if llm_client:
            print("  ✅ Enhanced LLM client initialized")
            available = llm_client.is_available()
            print(f"  📊 LLM client available: {available}")
        else:
            print("  ❌ Failed to initialize enhanced LLM client")
        
        # Test enhanced S3 client
        s3_client = get_enhanced_s3_client()
        if s3_client:
            print("  ✅ Enhanced S3 client initialized")
            available = s3_client.is_available()
            print(f"  📊 S3 client available: {available}")
        else:
            print("  ❌ Failed to initialize enhanced S3 client")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Enhanced client test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_key_generation():
    """Test master key generation."""
    print("\n🔑 Testing key generation...")
    
    try:
        from newsfrontier_lib.crypto import generate_master_key
        
        # Generate a new master key
        master_key = generate_master_key()
        
        if len(master_key) >= 32:
            print(f"  ✅ Generated master key: {master_key[:10]}...{master_key[-10:]}")
            print(f"  📏 Key length: {len(master_key)} characters")
        else:
            print(f"  ❌ Generated key too short: {len(master_key)} characters")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Key generation test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🧪 NewsFrontier Enhanced Encryption Test Suite")
    print("=" * 50)
    
    # Set up logging to suppress verbose output
    logging.getLogger().setLevel(logging.WARNING)
    
    tests = [
        ("Basic Encryption", test_basic_encryption),
        ("Configuration Service", test_configuration_service),
        ("Enhanced Clients", test_enhanced_clients),
        ("Key Generation", test_key_generation),
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
        print("🎉 All tests passed! Enhanced encryption is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the configuration and dependencies.")
        return 1


if __name__ == "__main__":
    exit(main())