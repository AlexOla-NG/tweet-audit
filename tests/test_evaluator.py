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
        
        with pytest.raises(RateLimitError) as excinfo:
            await evaluator.evaluate_batch([{"id": "1", "full_text": "test"}])
        
        assert "Gemini API rate limit reached" in str(excinfo.value)

@pytest.mark.asyncio
async def test_evaluate_batch_success():
    mock_response = MagicMock()
    mock_response.text = '["1", "3"]'
    
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
        
        flagged_ids = await evaluator.evaluate_batch(tweets)
        
        assert flagged_ids == ["1", "3"]
        mock_client.aio.models.generate_content.assert_called_once()

@pytest.mark.asyncio
async def test_evaluate_batch_markdown_json_response():
    mock_response = MagicMock()
    mock_response.text = '```json\n["1"]\n```'
    
    with patch("google.genai.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        
        evaluator = TweetEvaluator(api_key="test_key", criteria={})
        flagged_ids = await evaluator.evaluate_batch([{"id": "1", "full_text": "test"}])
        
        assert flagged_ids == ["1"]

@pytest.mark.asyncio
async def test_evaluate_batch_markdown_plain_response():
    mock_response = MagicMock()
    mock_response.text = '```\n["2"]\n```'
    
    with patch("google.genai.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        
        evaluator = TweetEvaluator(api_key="test_key", criteria={})
        flagged_ids = await evaluator.evaluate_batch([{"id": "2", "full_text": "test"}])
        
        assert flagged_ids == ["2"]

@pytest.mark.asyncio
async def test_evaluate_batch_invalid_json_logging(caplog):
    mock_response = MagicMock()
    mock_response.text = 'Not a JSON list'
    
    with patch("google.genai.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        
        evaluator = TweetEvaluator(api_key="test_key", criteria={})
        flagged_ids = await evaluator.evaluate_batch([{"id": "1", "full_text": "test"}])
        
        assert flagged_ids == []
        assert "Failed to decode JSON response from AI" in caplog.text

@pytest.mark.asyncio
async def test_default_model_selection():
    with patch("google.genai.Client") as mock_client_class:
        evaluator = TweetEvaluator(api_key="test_key", criteria={})
        assert evaluator.model_name == "gemini-2.5-flash"
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
