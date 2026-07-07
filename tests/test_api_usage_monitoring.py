import pytest
import requests
from api_usage_monitoring import monitor_api_usage
from unittest.mock import patch

def mock_requests_get(*args, **kwargs):
    """
    Mock function to replace requests.get during testing.
    """
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            self.elapsed = type('', (), {"total_seconds": lambda: 0.1})()  # Mock elapsed time

        def json(self):
            return self.json_data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")

    if args[0] == "https://jsonplaceholder.typicode.com/posts":
        return MockResponse([{"id": 1, "title": "Mock Post"}], 200)
    return MockResponse(None, 404)

@patch("requests.get", side_effect=mock_requests_get)
def test_monitor_api_usage(mock_get):
    """
    Test the monitor_api_usage function using a mocked API call.
    """
    response = monitor_api_usage("https://jsonplaceholder.typicode.com/posts", headers={}, params={})
    assert isinstance(response, list), "Response should be a list."
    assert len(response) > 0, "Response list should not be empty."
    assert response[0]["id"] == 1, "First post ID should match the mocked data."
    assert response[0]["title"] == "Mock Post", "Post title should match the mocked data."

    # Verify that the mock was called with the expected arguments
    mock_get.assert_called_with("https://jsonplaceholder.typicode.com/posts", headers={}, params={})
