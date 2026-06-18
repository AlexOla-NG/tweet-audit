import pytest
import os
import json
from src.parser import ArchiveParser
from tests.mock_data import MOCK_TWEETS_JS_CONTENT, MOCK_TWEETS_DATA

def test_archive_parser_success(tmp_path):
    # Create a temporary tweets.js file
    d = tmp_path / "data"
    d.mkdir()
    f = d / "tweets.js"
    f.write_text(MOCK_TWEETS_JS_CONTENT)

    parser = ArchiveParser(str(f))
    tweets = parser.parse()

    assert len(tweets) == len(MOCK_TWEETS_DATA)
    # The mock data returns the inner "tweet" object.
    assert tweets[0]["id"] == "1"
    assert tweets[0]["full_text"] == "I love crypto and NFTs! #hustle"

def test_archive_parser_file_not_found():
    parser = ArchiveParser("non_existent_file.js")
    with pytest.raises(FileNotFoundError):
        parser.parse()

def test_archive_parser_invalid_json(tmp_path):
    f = tmp_path / "invalid.js"
    f.write_text("window.invalid = [ { \"unclosed\": \"json\" ")

    parser = ArchiveParser(str(f))
    with pytest.raises(ValueError, match="Failed to decode JSON"):
        parser.parse()

def test_archive_parser_not_a_list(tmp_path):
    f = tmp_path / "not_list.js"
    f.write_text("window.YTD.tweet.part0 = { \"not\": \"a list\" }")

    parser = ArchiveParser(str(f))
    with pytest.raises(ValueError, match="Expected archive data to be a list"):
        parser.parse()
