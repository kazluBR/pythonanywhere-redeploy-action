import pytest
from unittest.mock import Mock, patch
from src.frameworks import (
    DjangoFramework,
    FlaskFramework,
    FrameworkFactory,
)
from src.pa_utils import PythonAnywhereUtils


@pytest.fixture
def mock_client():
    """Creates a mock PythonAnywhereClient."""
    client = Mock()
    client.send_input_to_console = Mock()
    client.get_latest_console_output = Mock(return_value={"output": "OK"})
    return client


@pytest.fixture
def web_app():
    """Sample web app dictionary."""
    return {
        "source_directory": "/home/user/myapp",
        "virtualenv_path": "/home/user/.virtualenvs/myapp",
    }


def test_factory_creates_django(mock_client, web_app):
    """Should create a DjangoFramework instance through the factory."""
    framework = FrameworkFactory.create("django", mock_client, 1, web_app, django_settings="mysettings")
    assert isinstance(framework, DjangoFramework)
    assert framework.django_settings == "mysettings"


def test_factory_creates_flask(mock_client, web_app):
    """Should create a FlaskFramework instance through the factory."""
    framework = FrameworkFactory.create("flask", mock_client, 1, web_app)
    assert isinstance(framework, FlaskFramework)


def test_django_run_commands(mock_client, web_app):
    """Should call expected Django console commands."""
    django = DjangoFramework(mock_client, 1, web_app, django_settings="mysite.settings")
    django.run_commands()

    calls = [call.args[1] for call in mock_client.send_input_to_console.call_args_list]
    assert any("activate" in cmd for cmd in calls)
    assert any("requirements.txt" in cmd for cmd in calls)
    assert any("manage.py migrate" in cmd for cmd in calls)


@patch("src.frameworks.info")
@patch.object(PythonAnywhereUtils, "parse_and_check_alembic", return_value=(True, "/home/user/myapp/migrations/alembic.ini"))
def test_flask_with_alembic(mock_parse, mock_info, mock_client, web_app):
    """Should detect Alembic and run migrations successfully."""
    flask = FlaskFramework(mock_client, 1, web_app)
    flask.run_commands()

    mock_parse.assert_called_once()
    mock_info.assert_any_call("Alembic configuration found, running migrations...")
    assert mock_client.send_input_to_console.call_count >= 4


@patch("src.frameworks.info")
@patch.object(PythonAnywhereUtils, "parse_and_check_alembic", return_value=(False, None))
def test_flask_without_alembic(mock_parse, mock_info, mock_client, web_app):
    """Should skip Alembic migrations if not found."""
    flask = FlaskFramework(mock_client, 1, web_app)
    flask.run_commands()

    mock_info.assert_any_call("No Alembic configuration found, skipping migrations.")


def test_factory_invalid_type(mock_client, web_app):
    """Should raise ValueError for unsupported framework types."""
    with pytest.raises(ValueError, match="not supported"):
        FrameworkFactory.create("unknown", mock_client, 1, web_app)
