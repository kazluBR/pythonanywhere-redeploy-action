import pytest
from unittest.mock import Mock, patch
from src.pa_utils import PythonAnywhereUtils


@pytest.fixture
def mock_client():
    """Creates a mock PythonAnywhereClient."""
    client = Mock()
    client.get_consoles = Mock()
    client.get_webapps = Mock()
    return client


@patch("src.pa_utils.info")
def test_setup_console_success(mock_info, mock_client):
    """Should find a valid bash console."""
    mock_client.get_consoles.return_value = [
        {"id": 1, "executable": "bash"},
        {"id": 2, "executable": "python"},
    ]

    console = PythonAnywhereUtils.setup_console(mock_client)
    assert console["id"] == 1
    mock_info.assert_any_call("Setting up console...")


def test_setup_console_no_bash(mock_client):
    """Should raise an exception if no bash/sh console is found."""
    mock_client.get_consoles.return_value = [{"id": 3, "executable": "python"}]

    with pytest.raises(Exception, match="No bash/sh console found"):
        PythonAnywhereUtils.setup_console(mock_client)


@patch("src.pa_utils.info")
def test_setup_web_app_with_domain(mock_info, mock_client):
    """Should find a matching web app by domain name."""
    mock_client.get_webapps.return_value = [
        {"domain_name": "app1.pythonanywhere.com"},
        {"domain_name": "app2.pythonanywhere.com"},
    ]

    app = PythonAnywhereUtils.setup_web_app(mock_client, "app2.pythonanywhere.com")
    assert app["domain_name"] == "app2.pythonanywhere.com"
    mock_info.assert_any_call("Setting up web app...")


def test_setup_web_app_no_match(mock_client):
    """Should raise an exception if domain is not found."""
    mock_client.get_webapps.return_value = [{"domain_name": "other.pythonanywhere.com"}]

    with pytest.raises(Exception, match="No matching web application found"):
        PythonAnywhereUtils.setup_web_app(mock_client, "missing.pythonanywhere.com")


def test_check_git_pull_output_scenarios():
    """Should correctly detect different git pull messages."""
    # Already up to date
    result = PythonAnywhereUtils.check_git_pull_output({"output": "Already up to date."})
    assert result == (True, None)

    # Local changes
    result = PythonAnywhereUtils.check_git_pull_output({"output": "Your local changes to the following files would be overwritten by merge"})
    assert result == (False, "local_changes")

    # Untracked files
    result = PythonAnywhereUtils.check_git_pull_output({"output": "untracked working tree files would be overwritten by merge"})
    assert result == (False, "untracked_files")

    # Generic error
    result = PythonAnywhereUtils.check_git_pull_output({"output": "error: merge conflict"})
    assert result == (False, "git_error")

    # Empty output
    result = PythonAnywhereUtils.check_git_pull_output({"output": ""})
    assert result == (True, None)


@patch("src.pa_utils.info")
def test_parse_and_check_alembic_found(mock_info):
    """Should detect an alembic.ini file path."""
    response = {"output": "/home/user/app/migrations/alembic.ini"}
    exists, path = PythonAnywhereUtils.parse_and_check_alembic(response)

    assert exists is True
    assert path.endswith("alembic.ini")
    mock_info.assert_any_call("Alembic configuration found!")


@patch("src.pa_utils.info")
def test_parse_and_check_alembic_not_found(mock_info):
    """Should handle missing alembic.ini."""
    response = {"output": "some random output without alembic"}
    exists, path = PythonAnywhereUtils.parse_and_check_alembic(response)

    assert exists is False
    assert path is None
    mock_info.assert_any_call("Alembic configuration not found, skipping migrations.")
