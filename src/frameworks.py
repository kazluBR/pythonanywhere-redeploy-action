import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from .pa_client import PythonAnywhereClient
from .github_utils import info, set_failed
from .pa_utils import PythonAnywhereUtils

class Framework(ABC):
    """Abstract base class for frameworks."""
    
    def __init__(self, client: PythonAnywhereClient, console_id: int, web_app: Dict[str, Any]):
        self.client = client
        self.console_id = console_id
        self.web_app = web_app
        self.source_directory = web_app['source_directory']
        self.virtualenv_path = web_app['virtualenv_path']

    @abstractmethod
    def run_commands(self):
        """Executes the framework-specific commands."""
        pass

    def _activate_venv(self):
        """Activates the virtual environment."""
        self.client.send_input_to_console(
            self.console_id,
            f"source {self.virtualenv_path}/bin/activate",
            "Virtual Environment Activated."
        )

    def _install_requirements(self):
        """Installs the dependencies."""
        self.client.send_input_to_console(
            self.console_id,
            f"pip install -r {self.source_directory}/requirements.txt",
            "Dependencies Installed."
        )

class DjangoFramework(Framework):
    """Implementation for the Django framework."""

    def __init__(self, client: PythonAnywhereClient, console_id: int, web_app: Dict[str, Any], django_settings: Optional[str] = None):
        super().__init__(client, console_id, web_app)
        self.django_settings = django_settings

    def run_commands(self):
        try:
            self._activate_venv()
            self._install_requirements()

            # Django migration command
            settings_arg = f' --settings={self.django_settings}' if self.django_settings else ''
            self.client.send_input_to_console(
                self.console_id,
                f"python {self.source_directory}/manage.py migrate{settings_arg}",
                "Database Migrations Completed."
            )
        except Exception as e:
            raise Exception(f"Error during console commands for Django: {e}")


class FlaskFramework(Framework):
    """Implementation for the Flask framework."""

    def run_commands(self):
        try:
            self._activate_venv()
            self._install_requirements()

            # Check Alembic
            self.client.send_input_to_console(
                self.console_id,
                f"find {self.source_directory} -type f -name 'alembic.ini' -print",
                "Checking for alembic.ini..."
            )

            alembic_response = self.client.get_latest_console_output(
                self.console_id,
                "Alembic check completed."
            )

            alembic_exists, alembic_path = PythonAnywhereUtils.parse_and_check_alembic(alembic_response)

            if alembic_exists and alembic_path:
                info("Alembic configuration found, running migrations...")
                alembic_dir = os.path.dirname(alembic_path)
                self.client.send_input_to_console(
                    self.console_id,
                    f"cd {alembic_dir} && alembic upgrade head",
                    "Executing 'alembic upgrade head'..."
                )
                alembic_upgrade_response = self.client.get_latest_console_output(
                    self.console_id,
                    "Alembic migration completed."
                )

                if "FAILED" in alembic_upgrade_response.get("output", ""):
                    set_failed("Alembic migration failed. Check your configuration.")
                    info(alembic_upgrade_response.get("output", ""))
                else:
                    info("Alembic migrations completed successfully.")
            else:
                info("No Alembic configuration found, skipping migrations.")
        except Exception as e:
            raise Exception(f"Error during console commands for Flask: {e}")


class FrameworkFactory:
    """Factory responsible for creating framework instances."""

    _registry = {
        "django": DjangoFramework,
        "flask": FlaskFramework
    }

    @classmethod
    def register_framework(cls, name: str, framework_cls: type):
        """Allows dynamic registration of new framework types."""
        cls._registry[name.lower()] = framework_cls

    @classmethod
    def create(cls, framework_type: str, client: PythonAnywhereClient, console_id: int, web_app: Dict[str, Any], **kwargs) -> Framework:
        framework_type = framework_type.lower()
        framework_cls = cls._registry.get(framework_type)

        if not framework_cls:
            raise ValueError(f"Framework type '{framework_type}' not supported.")

        # Pass any extra kwargs for frameworks that need it (e.g. Django)
        return framework_cls(client, console_id, web_app, **kwargs)

