"""
API Integration Tests for the intelligent chatbot.
Tests real API interactions with latency tracking.
"""
import pytest
import httpx
import time
from typing import List
from dataclasses import dataclass, field


API_BASE_URL = "http://0.0.0.0:8002"
TIMEOUT = 30.0


@dataclass
class ConversationMetrics:
    """Track conversation metrics."""
    total_requests: int = 0
    total_latency: float = 0.0
    successful_extractions: int = 0
    failed_extractions: int = 0
    latencies: List[float] = field(default_factory=list)
    
    def add_request(self, latency: float, success: bool = True):
        self.total_requests += 1
        self.total_latency += latency
        self.latencies.append(latency)
        if success:
            self.successful_extractions += 1
        else:
            self.failed_extractions += 1
    
    @property
    def avg_latency(self) -> float:
        return self.total_latency / self.total_requests if self.total_requests > 0 else 0.0
    
    @property
    def max_latency(self) -> float:
        return max(self.latencies) if self.latencies else 0.0
    
    @property
    def min_latency(self) -> float:
        return min(self.latencies) if self.latencies else 0.0


@pytest.fixture
def http_client():
    """Create HTTP client."""
    return httpx.Client(base_url=API_BASE_URL, timeout=TIMEOUT)


@pytest.fixture
def async_http_client():
    """Create async HTTP client."""
    return httpx.AsyncClient(base_url=API_BASE_URL, timeout=TIMEOUT)


def test_health_check(http_client):
    """Test API health check."""
    start = time.time()
    response = http_client.get("/")
    latency = time.time() - start
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print(f"\n✓ Health check passed (latency: {latency:.3f}s)")


@pytest.mark.asyncio
async def test_sentiment_analysis_conversation(async_http_client):
    """Test sentiment analysis through real conversation."""
    metrics = ConversationMetrics()
    conv_id = "test_sentiment_001"
    
    test_cases = [
        ("Hi, I want to book a car wash", "greeting", True),
        ("No,I'm not interested!", "service_selection", True),
        ("This is taking too long", "service_selection", True),
        ("I'm not sure about this", "tier_selection", True),
    ]
    
    print("\n" + "="*60)
    print("SENTIMENT ANALYSIS TEST")
    print("="*60)
    
    for message, state, should_succeed in test_cases:
        start = time.time()
        
        response = await async_http_client.post(
            "/chat",
            json={
                "conversation_id": conv_id,
                "user_message": message,
                "current_state": state
            }
        )
        
        latency = time.time() - start
        metrics.add_request(latency, response.status_code == 200)
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"\nUser: {message}")
        print(f"State: {state}")
        print(f"Sentiment: {data.get('sentiment', {})}")
        print(f"Should Proceed: {data.get('should_proceed')}")
        print(f"Latency: {latency:.3f}s")
    
    print(f"\n{'='*60}")
    print(f"Avg Latency: {metrics.avg_latency:.3f}s")
    print(f"Max Latency: {metrics.max_latency:.3f}s")
    print(f"Min Latency: {metrics.min_latency:.3f}s")
    print(f"Success Rate: {metrics.successful_extractions}/{metrics.total_requests}")


@pytest.mark.asyncio
async def test_name_extraction_conversation(async_http_client):
    """Test name extraction through real conversation."""
    metrics = ConversationMetrics()
    conv_id = "test_name_001"
    
    test_names = [
        "My name is Hrijul Dey",
        "I'm Ayush Raj",
        "Call me Abhishek Kabir",
        "You can call me Bodhi Singh"
    ]
    
    print("\n" + "="*60)
    print("NAME EXTRACTION TEST")
    print("="*60)
    
    for message in test_names:
        start = time.time()
        
        response = await async_http_client.post(
            "/chat",
            json={
                "conversation_id": conv_id,
                "user_message": message,
                "current_state": "name_collection"
            }
        )
        
        latency = time.time() - start
        
        assert response.status_code == 200
        data = response.json()
        extracted = data.get("extracted_data")
        
        success = extracted is not None
        metrics.add_request(latency, success)
        
        print(f"\nUser: {message}")
        print(f"Extracted: {extracted}")
        print(f"Response: {data.get('message', '')[:100]}")
        print(f"Latency: {latency:.3f}s")
    
    print(f"\n{'='*60}")
    print(f"Avg Latency: {metrics.avg_latency:.3f}s")
    print(f"Extraction Success: {metrics.successful_extractions}/{metrics.total_requests}")


@pytest.mark.asyncio
async def test_vehicle_extraction_conversation(async_http_client):
    """Test vehicle extraction through real conversation."""
    metrics = ConversationMetrics()
    conv_id = "test_vehicle_001"
    
    test_vehicles = [
        "I have a Tata Punch with plate number MH12AB1234",
        "It's a Mahindra Thar, plate is DL04C5678",
        "My car is Maruti Suzuki, number KA05ML9012",
        "I drive a Hyundai Creta, plate TN10XY3456"
    ]
    
    print("\n" + "="*60)
    print("VEHICLE EXTRACTION TEST")
    print("="*60)
    
    for message in test_vehicles:
        start = time.time()
        
        response = await async_http_client.post(
            "/chat",
            json={
                "conversation_id": conv_id,
                "user_message": message,
                "current_state": "vehicle_details"
            }
        )
        
        latency = time.time() - start
        
        assert response.status_code == 200
        data = response.json()
        extracted = data.get("extracted_data")
        
        success = extracted is not None
        metrics.add_request(latency, success)
        
        print(f"\nUser: {message}")
        print(f"Extracted: {extracted}")
        print(f"Latency: {latency:.3f}s")
    
    print(f"\n{'='*60}")
    print(f"Avg Latency: {metrics.avg_latency:.3f}s")
    print(f"Extraction Success: {metrics.successful_extractions}/{metrics.total_requests}")


@pytest.mark.asyncio
async def test_date_parsing_conversation(async_http_client):
    """Test date parsing through real conversation."""
    metrics = ConversationMetrics()
    conv_id = "test_date_001"
    
    test_dates = [
        "I want it tomorrow",
        "How about next Friday?",
        "Can we do it today?",
        "Next Wednesday works for me"
    ]
    
    print("\n" + "="*60)
    print("DATE PARSING TEST")
    print("="*60)
    
    for message in test_dates:
        start = time.time()
        
        response = await async_http_client.post(
            "/chat",
            json={
                "conversation_id": conv_id,
                "user_message": message,
                "current_state": "date_selection"
            }
        )
        
        latency = time.time() - start
        
        assert response.status_code == 200
        data = response.json()
        extracted = data.get("extracted_data")
        
        success = extracted is not None
        metrics.add_request(latency, success)
        
        print(f"\nUser: {message}")
        print(f"Extracted: {extracted}")
        print(f"Latency: {latency:.3f}s")
    
    print(f"\n{'='*60}")
    print(f"Avg Latency: {metrics.avg_latency:.3f}s")
    print(f"Extraction Success: {metrics.successful_extractions}/{metrics.total_requests}")


@pytest.mark.asyncio
async def test_full_conversation_flow(async_http_client):
    """Test complete conversation flow."""
    metrics = ConversationMetrics()
    conv_id = "test_full_001"
    
    conversation_flow = [
        ("Hi, I need a car wash", "greeting"),
        ("My name is John Doe", "name_collection"),
        ("I want a premium wash", "service_selection"),
        ("I have a Honda City, plate MH01AB1234", "vehicle_details"),
        ("Tomorrow afternoon works", "date_selection"),
    ]
    
    print("\n" + "="*60)
    print("FULL CONVERSATION FLOW TEST")
    print("="*60)
    
    for i, (message, state) in enumerate(conversation_flow, 1):
        start = time.time()
        
        response = await async_http_client.post(
            "/chat",
            json={
                "conversation_id": conv_id,
                "user_message": message,
                "current_state": state
            }
        )
        
        latency = time.time() - start
        metrics.add_request(latency, response.status_code == 200)
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"\n[Step {i}] User: {message}")
        print(f"State: {state}")
        print(f"Bot: {data.get('message', '')[:150]}")
        print(f"Extracted: {data.get('extracted_data')}")
        print(f"Latency: {latency:.3f}s")
    
    print(f"\n{'='*60}")
    print(f"Total Steps: {metrics.total_requests}")
    print(f"Avg Latency: {metrics.avg_latency:.3f}s")
    print(f"Total Time: {metrics.total_latency:.3f}s")
    print(f"Success Rate: {metrics.successful_extractions}/{metrics.total_requests}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
