"""
Quick test for the streaming chat API.
Run: python test_chat_api.py
"""
import requests
import json

def test_streaming_chat():
    url = "http://localhost:8002/api/chat"
    
    payload = {
        "messages": [
            {"role": "user", "content": "Hello, can you help me book an appointment?"}
        ],
        "session_id": "test-session"
    }
    
    print("Testing streaming chat API...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\nStreaming response:")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                print(decoded)
        
        print("-" * 50)
        print("✅ Test completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to backend.")
        print("Make sure the backend is running: uvicorn main:app --reload --port 8002")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_streaming_chat()
