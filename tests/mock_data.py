import json

def create_mock_tweet(tweet_id, text, created_at="Thu Jun 18 00:00:00 +0000 2026"):
    return {
        "tweet": {
            "edit_info": {
                "initial": {
                    "editTweetIds": [tweet_id],
                    "editableUntil": "2026-06-18T00:00:00.000Z",
                    "editsRemaining": "5",
                    "isEditEligible": True
                }
            },
            "retweeted": False,
            "source": "<a href=\"https://mobile.twitter.com\" rel=\"nofollow\">Twitter Web App</a>",
            "entities": {
                "hashtags": [],
                "symbols": [],
                "user_mentions": [],
                "urls": []
            },
            "display_text_range": ["0", str(len(text))],
            "favorite_count": "0",
            "id_str": tweet_id,
            "truncated": False,
            "retweet_count": "0",
            "id": tweet_id,
            "created_at": created_at,
            "favorited": False,
            "full_text": text,
            "lang": "en"
        }
    }

MOCK_TWEETS_DATA_LIST = [
    create_mock_tweet("1", "I love crypto and NFTs! #hustle"),
    create_mock_tweet("2", "This is a professional post about software engineering."),
    create_mock_tweet("3", "Old political opinion that I no longer hold."),
    create_mock_tweet("4", "Just a regular tweet about the weather."),
]

# Use json.dumps to ensure valid JSON (double quotes)
MOCK_TWEETS_JS_CONTENT = f"window.YTD.tweet.part0 = {json.dumps(MOCK_TWEETS_DATA_LIST)}"

# For testing ArchiveParser returns the inner "tweet" objects
MOCK_TWEETS_DATA = [entry["tweet"] for entry in MOCK_TWEETS_DATA_LIST]
