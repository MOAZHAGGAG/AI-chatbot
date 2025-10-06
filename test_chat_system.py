#!/usr/bin/env python3
"""
Comprehensive Test Suite for Helwan Commerce Chatbot
Tests chat history, validation, API integration, and UI components
"""

import sys
import os
import time
import json
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all modules can be imported successfully"""
    print("🧪 Testing Module Imports...")
    try:
        from response_validator import is_college_related_question
        from gemini_node import check_gemini_api_key, stream_gemini_response
        from dotenv import load_dotenv
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_env_setup():
    """Test environment configuration"""
    print("\n🧪 Testing Environment Setup...")
    from dotenv import load_dotenv
    load_dotenv()
    
    google_key = os.getenv('GOOGLE_API_KEY')
    if google_key:
        print(f"✅ Google API Key found (length: {len(google_key)})")
        return True
    else:
        print("❌ Google API Key not found in environment")
        return False

def test_question_validator():
    """Test the question validation system comprehensively"""
    print("\n🧪 Testing Question Validation System...")
    
    from response_validator import is_college_related_question
    
    # Test cases: (question, expected_result, description)
    test_cases = [
        # Arabic college questions (should pass)
        ("مصاريف BIS؟", True, "BIS fees in Arabic"),
        ("شروط القبول في نظام انتساب؟", True, "Admission requirements Arabic"),
        ("معلومات عن FMI؟", True, "FMI info in Arabic"),
        ("تفاصيل عن SBS؟", True, "SBS details in Arabic"),
        ("المصاريف كام للانتساب؟", True, "Fees question Arabic"),
        ("ازاي اقدم في الكلية؟", True, "Application process Arabic"),
        
        # English college questions (should pass)
        ("What are BIS program fees?", True, "BIS fees in English"),
        ("How to apply to the college?", True, "Application in English"),
        ("Tell me about FMI program", True, "FMI info in English"),
        ("Admission requirements?", True, "Requirements in English"),
        
        # Mixed/Short questions (should pass)
        ("BIS", True, "Single word - program name"),
        ("مصاريف؟", True, "Single word - fees"),
        ("القبول", True, "Single word - admission"),
        
        # Non-college questions (should fail)
        ("What is the weather today?", False, "Weather question"),
        ("Who is the president?", False, "Political question"),
        ("How to cook pasta?", False, "Cooking question"),
        ("Tell me a joke", False, "Entertainment request"),
        ("What is Python?", False, "Programming question"),
        ("How old are you?", False, "Personal question"),
        
        # Edge cases
        ("", False, "Empty string"),
        ("   ", False, "Whitespace only"),
        ("123456", False, "Numbers only"),
        ("!@#$%", False, "Special characters only"),
    ]
    
    passed = 0
    failed = 0
    
    print(f"Running {len(test_cases)} validation tests...")
    
    for question, expected, description in test_cases:
        try:
            result = is_college_related_question(question)
            if result == expected:
                print(f"✅ PASS: {description} -> {result}")
                passed += 1
            else:
                print(f"❌ FAIL: {description} -> Expected {expected}, got {result}")
                print(f"   Question: '{question}'")
                failed += 1
        except Exception as e:
            print(f"💥 ERROR: {description} -> {e}")
            failed += 1
    
    print(f"\n📊 Validation Results: {passed} passed, {failed} failed")
    return failed == 0

def test_gemini_api():
    """Test Gemini API functionality"""
    print("\n🧪 Testing Gemini API...")
    
    from gemini_node import check_gemini_api_key, stream_gemini_response
    
    # Test API key
    if not check_gemini_api_key():
        print("❌ Gemini API key check failed")
        return False
    
    print("✅ Gemini API key validated")
    
    # Test simple response
    try:
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant. Answer in one sentence."},
            {"role": "user", "content": "Say hello in Arabic"}
        ]
        
        print("Testing streaming response...")
        full_response = ""
        response_chunks = 0
        
        for chunk in stream_gemini_response(test_messages, model="gemini-2.0-flash-lite", temperature=0.7):
            full_response += chunk
            response_chunks += 1
            if response_chunks > 50:  # Prevent infinite loops
                break
        
        if full_response and len(full_response) > 5:
            print(f"✅ Streaming response successful ({response_chunks} chunks)")
            print(f"   Response: {full_response[:100]}...")
            return True
        else:
            print("❌ Empty or too short response")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_info_file():
    """Test college information file"""
    print("\n🧪 Testing College Info File...")
    
    try:
        with open("info.txt", "r", encoding="utf-8") as f:
            content = f.read()
        
        if len(content) < 100:
            print("❌ Info file too short")
            return False
        
        # Check for key information
        key_terms = ["BIS", "FMI", "SBS", "مصاريف", "القبول", "جامعة حلوان"]
        found_terms = [term for term in key_terms if term in content]
        
        print(f"✅ Info file loaded ({len(content)} chars)")
        print(f"✅ Key terms found: {found_terms}")
        
        return len(found_terms) >= 4
        
    except Exception as e:
        print(f"❌ Info file test failed: {e}")
        return False

def test_session_state_simulation():
    """Simulate session state behavior"""
    print("\n🧪 Testing Session State Simulation...")
    
    # Simulate Streamlit session state
    class MockSessionState:
        def __init__(self):
            self.data = {}
        
        def __getattr__(self, key):
            if key in self.data:
                return self.data[key]
            raise AttributeError(f"'{key}' not found in session state")
        
        def __setattr__(self, key, value):
            if key == 'data':
                super().__setattr__(key, value)
            else:
                self.data[key] = value
    
    # Test session state operations
    try:
        session = MockSessionState()
        
        # Test initialization
        if not hasattr(session, 'messages'):
            session.messages = []
        
        # Test adding messages
        session.messages.append({"role": "user", "content": "Test message"})
        session.messages.append({"role": "assistant", "content": "Test response"})
        
        # Test retrieval
        assert len(session.messages) == 2
        assert session.messages[0]["role"] == "user"
        assert session.messages[1]["role"] == "assistant"
        
        print("✅ Session state simulation successful")
        return True
        
    except Exception as e:
        print(f"❌ Session state test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and generate report"""
    print("🚀 Starting Comprehensive Chatbot Tests")
    print("=" * 50)
    
    test_results = {}
    
    # Run all tests
    tests = [
        ("Module Imports", test_imports),
        ("Environment Setup", test_env_setup),
        ("Question Validator", test_question_validator),
        ("Gemini API", test_gemini_api),
        ("Info File", test_info_file),
        ("Session State", test_session_state_simulation),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results[test_name] = "PASS" if result else "FAIL"
        except Exception as e:
            test_results[test_name] = f"ERROR: {e}"
    
    # Generate report
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, result in test_results.items():
        status_emoji = "✅" if result == "PASS" else "❌"
        print(f"{status_emoji} {test_name}: {result}")
        if result == "PASS":
            passed_tests += 1
    
    print(f"\n🎯 Overall Score: {passed_tests}/{total_tests} tests passed")
    
    # Recommendations
    print("\n🔧 RECOMMENDATIONS:")
    if test_results.get("Question Validator") != "PASS":
        print("- Review and improve question validation logic")
    if test_results.get("Gemini API") != "PASS":
        print("- Check Gemini API configuration and error handling")
    if test_results.get("Info File") != "PASS":
        print("- Verify college information file completeness")
    
    return passed_tests, total_tests

if __name__ == "__main__":
    passed, total = run_all_tests()
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "passed": passed,
        "total": total,
        "success_rate": (passed / total) * 100
    }
    
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📝 Results saved to test_results.json")
    
    # Exit code for CI/CD
    sys.exit(0 if passed == total else 1)