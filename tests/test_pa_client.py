import pytest
import requests
import requests_mock
from unittest.mock import patch
from src.pa_client import PythonAnywhereClient


@pytest.fixture
def client():
    """Creates a test instance of the PythonAnywhere client."""
    return PythonAnywhereClient(
        username="testuser",
        token="testtoken",
        host="www.pythonanywhere.com"
    )


@patch("src.pa_client.info")
def test_request_success(mock_info, client):
    """Should return JSON data on successful GET request."""
    with requests_mock.Mocker() as m:
        url = f"{client.base_api_url}/consoles/"
        m.get(url, json=[{"id": 1}], status_code=200)

        response = client._request("GET", "/consoles/")
        assert response == [{"id": 1}]
        mock_info.assert_called_once_with(f"Sending GET request to: {url}")


def test_request_http_error_with_json_error(client):
    """Should raise an exception with API error message."""
    with requests_mock.Mocker() as m:
        url = f"{client.base_api_url}/consoles/"
        m.get(url, json={"error": "Invalid request"}, status_code=400)

        with pytest.raises(Exception, match="Invalid request"):
            client._request("GET", "/consoles/")


@patch("src.pa_client.info")
def test_get_latest_console_output_with_retries(mock_info, client):
    """Should retry failed requests and succeed on the third attempt."""
    with patch("time.sleep", return_value=None):
        with requests_mock.Mocker() as m:
            console_id = 42
            url = f"{client.base_api_url}/consoles/{console_id}/get_latest_output/"
            # First 2 attempts fail, 3rd one succeeds
            m.get(url, [
                {"exc": requests.exceptions.RequestException("Timeout")},
                {"exc": requests.exceptions.RequestException("Timeout")},
                {"json": {"output": "OK"}, "status_code": 200},
            ])

            response = client.get_latest_console_output(console_id, "Success")
            assert response == {"output": "OK"}
            mock_info.assert_any_call("Success")


@patch("src.pa_client.info")
def test_send_input_to_console(mock_info, client):
    """Should send command input to console successfully."""
    with requests_mock.Mocker() as m:
        console_id = 99
        url = f"{client.base_api_url}/consoles/{console_id}/send_input/"
        m.post(url, json={}, status_code=200)

        client.send_input_to_console(console_id, "ls -la", "Done")
        mock_info.assert_any_call("Running command: ls -la")
        mock_info.assert_any_call("Done")
