import json
import logging
from pathlib import Path
from google import genai
from typing import List, Dict, Optional

# Configure logging
logger = logging.getLogger("tweet-audit.evaluator")

class RateLimitError(Exception):
    """Raised when the AI API rate limit is exceeded."""
    pass

class TweetEvaluator:
    def __init__(self, api_key: str, criteria: Dict, model_name: str = 'gemini-3.1-flash-lite'):
        self.api_key = api_key
        self.criteria = criteria
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key)

    def _read_workspace_file(self, filename: str) -> str:
        repo_root = Path(__file__).resolve().parent.parent
        file_path = repo_root / filename
        if not file_path.exists():
            return ""

        with file_path.open("r", encoding="utf-8") as handle:
            return handle.read()

    def _load_json_file(self, filename: str) -> Dict:
        content = self._read_workspace_file(filename)
        if not content:
            return {}
        return json.loads(content)

    def _build_prompt(self, tweets: List[Dict]) -> str:
        criteria_str = json.dumps(self.criteria, indent=2)
        input_prompt = self._read_workspace_file("input_prompt.md")
        scoring_model = self._load_json_file("scoring_model.json")
        output_schema = self._load_json_file("output_schema.json")

        tweets_data = []
        for t in tweets:
            tweets_data.append({
                "id": t.get("id_str") or t.get("id"),
                "text": t.get("full_text", "")
            })
        
        tweets_str = json.dumps(tweets_data, indent=2)

        prompt = f"""
Follow the instructions in input_prompt.md exactly.

You must use the scoring weights in scoring_model.json to calculate risk scores and determine the classification bucket for each tweet.
You must also follow the exact field structure and allowed values in output_schema.json.
If the output schema conflicts with the earlier instructions, follow the output schema.

Input Prompt (from input_prompt.md):
{input_prompt}

Scoring Model (from scoring_model.json):
{json.dumps(scoring_model, indent=2)}

Output Schema (from output_schema.json):
{json.dumps(output_schema, indent=2)}

Analyze the following list of tweets against the provided alignment criteria.
Return ONLY a JSON array of objects matching the output schema.
Each object must include the fields defined in the schema and values that conform to the schema.

If no tweets violate the criteria, return an empty list [].
Do not include any explanation or other text.

Alignment Criteria:
{criteria_str}

Tweets to analyze:
{tweets_str}
"""
        return prompt

    def estimate_tokens(self, tweets: List[Dict]) -> int:
        """Conservative estimation of tokens in the prompt."""
        prompt = self._build_prompt(tweets)
        # Conservative estimate: ~3 characters per token
        return len(prompt) // 3

    def _normalize_schema_item(self, item: Dict) -> Optional[Dict]:
        if not isinstance(item, dict):
            return None

        item_id = item.get("id")
        if item_id is None and "tweet_url" in item:
            tweet_url = str(item["tweet_url"]).strip()
            if tweet_url.isdigit():
                item_id = tweet_url
            elif "/status/" in tweet_url:
                item_id = tweet_url.split("/status/")[-1].split("?")[0].split("#")[0]

        if item_id is None:
            return None

        normalized = {"id": str(item_id)}
        schema_fields = {"tweet_url", "label", "risk_score", "primary_issue", "suggested_action"}
        uses_schema_shape = any(field in item for field in schema_fields)

        if "tweet_url" in item:
            normalized["tweet_url"] = str(item["tweet_url"])

        if "label" in item:
            normalized["label"] = str(item["label"]).strip().lower()

        if "risk_score" in item:
            try:
                normalized["risk_score"] = int(item["risk_score"])
            except (TypeError, ValueError):
                normalized["risk_score"] = 0

        if "primary_issue" in item:
            normalized["primary_issue"] = str(item["primary_issue"]).strip().lower()

        if "reason" in item:
            normalized["reason"] = str(item["reason"])

        if "suggested_action" in item:
            normalized["suggested_action"] = str(item["suggested_action"])

        if "confidence" in item:
            conf = item["confidence"]
            if isinstance(conf, str):
                conf_text = conf.strip()
                if uses_schema_shape:
                    conf_value = conf_text.lower()
                    if conf_value not in {"low", "medium", "high"}:
                        conf_value = "medium"
                else:
                    conf_value = conf_text.capitalize()
                    if conf_value not in {"High", "Medium", "Low"}:
                        conf_value = "Medium"
            else:
                conf_value = "medium" if uses_schema_shape else "Medium"
        else:
            conf_value = "medium" if uses_schema_shape else "Medium"

        normalized["confidence"] = conf_value

        return normalized

    async def evaluate_batch(self, tweets: List[Dict]) -> tuple[List[Dict[str, str]], int]:
        """Evaluates a batch of tweets and returns (flagged_objects, total_tokens)."""
        if not tweets:
            return [], 0

        prompt = self._build_prompt(tweets)
        
        try:
            # Using the new google-genai async client
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            text = response.text.strip()
            
            # Extract actual token usage
            total_tokens = 0
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                total_tokens = response.usage_metadata.total_token_count or 0
            
            # Robust JSON extraction from markdown code blocks
            if "```" in text:
                parts = text.split("```")
                if len(parts) >= 3:
                    text = parts[1].strip()
                    if text.startswith("json"):
                        text = text[4:].strip()
            
            flagged_items = json.loads(text)
            if not isinstance(flagged_items, list):
                logger.warning(f"Unexpected response format from AI (not a list): {text}")
                return [], total_tokens
            
            validated_items = []
            for item in flagged_items:
                normalized_item = self._normalize_schema_item(item)
                if normalized_item is None:
                    logger.warning(f"Skipping malformed flagged item: {item}")
                    continue

                if "id" not in normalized_item:
                    logger.warning(f"Skipping malformed flagged item: {item}")
                    continue

                validated_items.append(normalized_item)
            
            return validated_items, total_tokens
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response from AI: {e}. Raw text: {text}")
            return [], total_tokens
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                logger.error(f"Rate limit exceeded: {error_msg}")
                raise RateLimitError(f"Gemini API rate limit reached: {error_msg}")
            
            logger.error(f"Error during AI evaluation: {e}", exc_info=True)
            return [], 0

    async def close(self):
        """Closes the underlying async client."""
        await self.client.aio.aclose()
