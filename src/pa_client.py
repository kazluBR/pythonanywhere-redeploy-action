"""
PythonAnywhere API Client

This module provides a wrapper around the PythonAnywhere REST API to manage consoles and web apps.

Based on the PythonAnywhere API (beta) documentation:
https://help.pythonanywhere.com/pages/API/
"""

import requests
import json
import time
from typing import Optional, Dict, Any
from .github_utils import info

class PythonAnywhereClient:
    """A client to interact with the PythonAnywhere API."""

    def __init__(self, username: str, token: str, host: str):
        self.username = username
        self.token = token
        self.host = host
        self.base_api_url = f"https://{self.host}/api/v0/user/{self.username}"
        self.headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Performs a generic request to the API."""
        url = f"{self.base_api_url}{path}"
        info(f"Sending {method} request to: {url}")
        
        try:
            response = requests.request(method, url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            error_message = f"API Error: {e.response.status_code} - {e.response.text}"
            if e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    if "error" in error_data:
                        error_message = error_data["error"]
                except json.JSONDecodeError:
                    pass
            raise Exception(error_message)
        except Exception as e:
            raise Exception(f"Request to {url} failed: {e}")

    def get_consoles(self) -> list:
        """Lists the user's consoles."""
        return self._request("GET", "/consoles/")

    def get_latest_console_output(self, console_id: int, success_msg: str) -> Dict[str, Any]:
        """Gets the latest console output, with retries."""
        console_output_url = f"/consoles/{console_id}/get_latest_output/"
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = self._request("GET", console_output_url)
                info(success_msg)
                return response
            except Exception as e:
                if attempt < max_retries - 1:
                    info(f"Attempt {attempt + 1} failed to get console output. Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    raise Exception(f"Failed to get console output after {max_retries} attempts: {e}")

    def send_input_to_console(self, console_id: int, command: str, success_msg: str):
        """Sends a command to the console."""
        console_request_url = f"/consoles/{console_id}/send_input/"
        payload = {"input": f"{command}\n"}
        info(f"Running command: {command}")
        self._request("POST", console_request_url, data=payload)
        info(success_msg)

    def get_webapps(self) -> list:
        """Lists the user's webapps."""
        return self._request("GET", "/webapps/")

    def reload_webapp(self, domain_name: str):
        """Reloads a webapp."""
        self._request("POST", f"/webapps/{domain_name}/reload/")
