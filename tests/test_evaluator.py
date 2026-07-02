import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from src.evaluator import TweetEvaluator, RateLimitError

@pytest.mark.asyncio
async def test_evaluate_batch_rate_limit():
    with patch("google.genai.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        # Simulate a 429 error from the SDK
        mock_client.aio.models.generate_content = AsyncMock(side_effect=Exception("429 RESOURCE_EXHAUSTED"))
        
        evaluator = TweetEvaluator(api_key="test_key", criteria={})
        
        with pytest.raises(RateLimitError):
            await evaluator.evaluate_batch([{"id": "1", "full_text": "test"}])

@pytest.mark.asyncio
async def test_evaluate_batch_success():
    mock_response = MagicMock()
    mock_response.text = '[{"id": "1", "reason": "unprofessional", "confidence": "High"}, {"id": "3", "reason": "offensive", "confidence": "Medium"}]'
    mock_response.usage_metadata.total_token_count = 100
    
    with patch("google.genai.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        
        criteria = {"forbidden_words": ["crypto"]}
        evaluator = TweetEvaluator(api_key="test_key", criteria=criteria)
        
        tweets = [
            {"id": "1", "full_text": "I love crypto"},
            {"id": "2", "full_text": "Good morning"},
            {"id": "3", "full_text": "NFT is the future"}
        ]
        
        flagged_items, total_tokens = await evaluator.evaluate_batch(tweets)
        
        assert flagged_items == [
            {"id": "1", "reason": "unprofessional", "confidence": "High"},
            {"id": "3", "reason": "offensive", "confidence": "Medium"}
        ]
        assert total_tokens == 100
        mock_client.aio.models.generate_content.assert_called_once()

@pytest.mark.asyncio
async def test_evaluate_batch_markdown_json_response():
    mock_response = MagicMock()
    mock_response.text = '```json\n[{"id": "1", "reason": "test", "confidence": "high"}]\n```'
    mock_response.usage_metadata.total_token_count = 50
    
    with patch("google.genai.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        
        evaluator = TweetEvaluator(api_key="test_key", criteria={})
        flagged_items, total_tokens = await evaluator.evaluate_batch([{"id": "1", "full_text": "test"}])
        
        assert flagged_items == [{"id": "1", "reason": "test", "confidence": "High"}]
        assert total_tokens == 50

@pytest.mark.asyncio
async def test_evaluate_batch_markdown_plain_response():
    mock_response = MagicMock()
    mock_response.text = '```\n[{"id": "2", "reason": "test2", "confidence": "low"}]\n```'
    mock_response.usage_metadata.total_token_count = 60
    
    with patch("google.genai.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        
        evaluator = TweetEvaluator(api_key="test_key", criteria={})
        flagged_items, total_tokens = await evaluator.evaluate_batch([{"id": "2", "full_text": "test"}])
        
        assert flagged_items == [{"id": "2", "reason": "test2", "confidence": "Low"}]
        assert total_tokens == 60

@pytest.mark.asyncio
async def test_evaluate_batch_confidence_fallback():
    mock_response = MagicMock()
    # "id" 1 is missing confidence, "id" 2 has invalid confidence, "id" 3 has non-string confidence
    mock_response.text = '[{"id": "1", "reason": "r1"}, {"id": "2", "reason": "r2", "confidence": "invalid"}, {"id": "3", "reason": "r3", "confidence": 123}]'
    mock_response.usage_metadata.total_token_count = 30
    
    with patch("google.genai.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        
        evaluator = TweetEvaluator(api_key="test_key", criteria={})
        flagged_items, total_tokens = await evaluator.evaluate_batch([{"id": "1"}, {"id": "2"}, {"id": "3"}])
        
        assert flagged_items == [
            {"id": "1", "reason": "r1", "confidence": "Medium"},
            {"id": "2", "reason": "r2", "confidence": "Medium"},
            {"id": "3", "reason": "r3", "confidence": "Medium"}
        ]

@pytest.mark.asyncio
async def test_evaluate_batch_invalid_json_logging(caplog):
    mock_response = MagicMock()
    mock_response.text = 'Not a JSON list'
    mock_response.usage_metadata.total_token_count = 10
    
    with patch("google.genai.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        
        evaluator = TweetEvaluator(api_key="test_key", criteria={})
        flagged_items, total_tokens = await evaluator.evaluate_batch([{"id": "1", "full_text": "test"}])
        
        assert flagged_items == []
        assert total_tokens == 10
        assert "Failed to decode JSON response from AI" in caplog.text

@pytest.mark.asyncio
async def test_default_model_selection():
    with patch("google.genai.Client") as mock_client_class:
        evaluator = TweetEvaluator(api_key="test_key", criteria={})
        assert evaluator.model_name == "gemini-3.1-flash-lite"
        mock_client_class.assert_called_once_with(api_key="test_key")

@pytest.mark.asyncio
async def test_custom_model_selection():
    with patch("google.genai.Client") as mock_client_class:
        evaluator = TweetEvaluator(api_key="test_key", criteria={}, model_name="gemini-2.0-pro")
        assert evaluator.model_name == "gemini-2.0-pro"
        mock_client_class.assert_called_once_with(api_key="test_key")

@pytest.mark.asyncio
async def test_close_client():
    with patch("google.genai.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.aio.aclose = AsyncMock()
        
        evaluator = TweetEvaluator(api_key="test_key", criteria={})
        await evaluator.close()
        
        mock_client.aio.aclose.assert_called_once()
