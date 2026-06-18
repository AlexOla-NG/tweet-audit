import json
import logging
from google import genai
from typing import List, Dict, Optional

# Configure logging
logger = logging.getLogger("tweet-audit.evaluator")

class TweetEvaluator:
    def __init__(self, api_key: str, criteria: Dict, model_name: str = 'gemini-2.5-flash'):
        self.api_key = api_key
        self.criteria = criteria
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key)

    def _build_prompt(self, tweets: List[Dict]) -> str:
        criteria_str = json.dumps(self.criteria, indent=2)
        tweets_data = []
        for t in tweets:
            tweets_data.append({
                "id": t.get("id_str") or t.get("id"),
                "text": t.get("full_text", "")
            })
        
        tweets_str = json.dumps(tweets_data, indent=2)

        prompt = f"""
Analyze the following list of tweets against the provided alignment criteria.
Return ONLY a JSON list of tweet IDs that SHOULD BE DELETED because they violate the criteria.
If no tweets violate the criteria, return an empty list [].
Do not include any explanation or other text.

Alignment Criteria:
{criteria_str}

Tweets to analyze:
{tweets_str}

Format your response exactly like this:
["id1", "id2", ...]
"""
        return prompt

    async def evaluate_batch(self, tweets: List[Dict]) -> List[str]:
        """Evaluates a batch of tweets and returns IDs that should be deleted."""
        if not tweets:
            return []

        prompt = self._build_prompt(tweets)
        
        try:
            # Using the new google-genai async client
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            text = response.text.strip()
            
            # Robust JSON extraction from markdown code blocks
            if "```" in text:
                parts = text.split("```")
                if len(parts) >= 3:
                    text = parts[1].strip()
                    if text.startswith("json"):
                        text = text[4:].strip()
            
            flagged_ids = json.loads(text)
            if not isinstance(flagged_ids, list):
                logger.warning(f"Unexpected response format from AI (not a list): {text}")
                return []
            
            return [str(fid) for fid in flagged_ids]
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response from AI: {e}. Raw text: {text}")
            return []
        except Exception as e:
            logger.error(f"Error during AI evaluation: {e}", exc_info=True)
            return []

    async def close(self):
        """Closes the underlying async client."""
        await self.client.aio.aclose()
