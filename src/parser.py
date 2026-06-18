import json
import os

class ArchiveParser:
    def __init__(self, file_path):
        self.file_path = file_path

    def parse(self):
        """Parses the tweets.js file and returns a list of tweet objects."""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Archive file not found: {self.file_path}")

        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove the JavaScript prefix (e.g., window.YTD.tweet.part0 = )
        # Find the first occurrence of '[' or '{'
        start_index_bracket = content.find('[')
        start_index_brace = content.find('{')
        
        if start_index_bracket == -1 and start_index_brace == -1:
            raise ValueError("Could not find start of JSON data in archive file.")
        
        # Use the earliest index found
        if start_index_bracket == -1:
            start_index = start_index_brace
        elif start_index_brace == -1:
            start_index = start_index_bracket
        else:
            start_index = min(start_index_bracket, start_index_brace)
        
        json_content = content[start_index:]
        
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to decode JSON from archive: {e}")

        if not isinstance(data, list):
            raise ValueError(f"Expected archive data to be a list, got {type(data).__name__}")

        # Each entry is usually {"tweet": {...}}
        tweets = []
        for entry in data:
            if isinstance(entry, dict) and "tweet" in entry:
                tweets.append(entry["tweet"])
        
        return tweets
