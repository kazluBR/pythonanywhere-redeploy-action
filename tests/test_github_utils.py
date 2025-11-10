import os
from unittest.mock import patch
from src.github_utils import get_input, set_failed, info


@patch("builtins.print")
def test_info_prints_github_notice(mock_print):
    """Should print a GitHub Actions notice message."""
    info("Deployment started")
    mock_print.assert_called_once_with("::notice::Deployment started")


@patch("builtins.print")
@patch("sys.exit")
def test_set_failed_prints_error_and_exits(mock_exit, mock_print):
    """Should print a GitHub Actions error message and exit with code 1."""
    set_failed("Invalid input")
    mock_print.assert_called_once_with("::error::Invalid input")
    mock_exit.assert_called_once_with(1)


@patch("src.github_utils.set_failed")
def test_get_input_returns_value_from_env(mock_set_failed):
    """Should return environment variable value when defined."""
    os.environ["INPUT_USERNAME"] = "lucas"
    result = get_input("username")
    assert result == "lucas"
    mock_set_failed.assert_not_called()


@patch("src.github_utils.set_failed")
def test_get_input_calls_set_failed_when_required_and_missing(mock_set_failed):
    """Should call set_failed when required input is missing."""
    os.environ.pop("INPUT_PASSWORD", None)
    get_input("password", required=True)
    mock_set_failed.assert_called_once_with("Input required and not supplied: password")


@patch("src.github_utils.set_failed")
def test_get_input_returns_default_when_not_required(mock_set_failed):
    """Should return default value when input is optional and missing."""
    os.environ.pop("INPUT_TOKEN", None)
    result = get_input("token", required=False, default="default_token")
    assert result == "default_token"
    mock_set_failed.assert_not_called()
