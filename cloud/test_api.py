"""
Simple API test script
Verifies backend is running and working correctly
"""

import requests
import json
import sys

API_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_URL}/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(f"   Model: {data['model']}")
            print(f"   RAG Agent: {data['rag_agent']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_ask():
    """Test ask endpoint"""
    print("\nTesting ask endpoint...")
    try:
        payload = {
            "question": "What are Autopools?",
            "user_id": "test_user_123",
            "user_name": "Test User",
            "user_email": "test@example.com"
        }
        
        response = requests.post(
            f"{API_URL}/api/ask",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Ask endpoint passed")
            print(f"   Answer length: {len(data['answer'])} characters")
            print(f"   Model: {data['model']}")
            print(f"\n   Answer preview:")
            print(f"   {data['answer'][:200]}...")
            return True
        else:
            print(f"❌ Ask endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ask endpoint failed: {e}")
        return False

def test_stats():
    """Test stats endpoint"""
    print("\nTesting stats endpoint...")
    try:
        response = requests.get(f"{API_URL}/api/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stats endpoint passed")
            print(f"   Total conversations: {data['total_conversations']}")
            print(f"   Unique users: {data['unique_users']}")
            return True
        else:
            print(f"❌ Stats endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stats endpoint failed: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 Auto Finance Bot API Test")
    print("=" * 60)
    print()
    
    # Test connection
    print("Checking API connection...")
    try:
        response = requests.get(f"{API_URL}/")
        if response.status_code != 200:
            print(f"❌ API not responding at {API_URL}")
            print("\nMake sure the backend is running:")
            print("  python run_local.py")
            print("  OR")
            print("  docker-compose up")
            sys.exit(1)
        print(f"✅ API is running at {API_URL}")
        print()
    except Exception as e:
        print(f"❌ Cannot connect to API at {API_URL}")
        print(f"   Error: {e}")
        print("\nMake sure the backend is running:")
        print("  python run_local.py")
        print("  OR")
        print("  docker-compose up")
        sys.exit(1)
    
    # Run tests
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Stats Endpoint", test_stats()))
    results.append(("Ask Question", test_ask()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print()
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your API is working correctly.")
        print("\nNext step: Open http://localhost:3000 in your browser")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

