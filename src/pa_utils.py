from typing import Optional, Dict, Any, Tuple
from .github_utils import info
from .pa_client import PythonAnywhereClient

class PythonAnywhereUtils:
    """
    Utility class for auxiliary configuration and verification functions
    specific to the PythonAnywhere environment.
    """

    @staticmethod
    def setup_console(client: PythonAnywhereClient) -> Dict[str, Any]:
        """Configures or finds an existing bash/sh console."""
        info("Setting up console...")
        console_list_data = client.get_consoles()
        
        if isinstance(console_list_data, list) and console_list_data:
            valid_console = next((c for c in console_list_data if c.get("executable") in ["bash", "sh"]), None)
            if valid_console:
                info(f"Console found with ID: {valid_console['id']}")
                return valid_console
            
        raise Exception("No bash/sh console found. Please create one in your PythonAnywhere account.")

    @staticmethod
    def setup_web_app(client: PythonAnywhereClient, domain_name: Optional[str]) -> Dict[str, Any]:
        """Finds the web app to be re-deployed."""
        info("Setting up web app...")
        webapp_list_data = client.get_webapps()
        
        if not (isinstance(webapp_list_data, list) and webapp_list_data):
            raise Exception("No web applications found. Check your application or account details!")

        if domain_name:
            web_app = next((app for app in webapp_list_data if app.get("domain_name") == domain_name), None)
            if not web_app:
                raise Exception(f"No matching web application found for domain: {domain_name}")
        else:
            web_app = webapp_list_data[0]
            info(f"No domain name specified. Using the first web app: {web_app.get('domain_name')}")
            
        info(f"Web app '{web_app.get('domain_name')}' selected.")
        return web_app

    @staticmethod
    def check_git_pull_output(response: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Checks the output of the git pull command."""
        output = response.get("output", "")
        
        if not output:
            return True, None

        lines = [line.strip() for line in output.splitlines() if line.strip()]

        if any("Already up to date" in line for line in lines):
            info("Repository is already up to date.")
            return True, None

        if any("Your local changes to the following files would be overwritten by merge" in line for line in lines):
            return False, "local_changes"
        
        if any("untracked working tree files would be overwritten by merge" in line for line in lines):
            return False, "untracked_files"
        
        if any(line.startswith("error:") for line in lines):
            return False, "git_error"

        return True, None

    @staticmethod
    def upload_env_file(client: PythonAnywhereClient, console_id: int, web_app: Dict[str, Any], envs: Dict[str, str]):
        """
        Creates a .env file content and uploads it to the web app's source directory
        using the console.
        """
        info("Uploading .env file with provided environment variables...")
        
        env_content = ""
        for key, value in envs.items():
            # Escape single quotes in the value to prevent command injection
            escaped_value = value.replace("'", "'\\''")
            env_content += f"{key}='{escaped_value}'\n"

        # The final command will be: echo 'KEY1=VALUE1\nKEY2=VALUE2\n' > /path/to/source/.env
        upload_command = (
            f"cat > {web_app['source_directory']}/.env << 'EOF'\n"
            f"{env_content}"
            "EOF"
        )
        
        client.send_input_to_console(
            console_id,
            upload_command,
            "'.env' file uploaded successfully."
        )
        
        info("Environment variables written to .env file on PythonAnywhere.")

    @staticmethod
    def parse_and_check_alembic(response: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Checks the output of the alembic.ini search command."""
        output = response.get("output", "")

        if not output:
            info("No output found in the response for Alembic check.")
            return False, None

        lines = [line.strip() for line in output.splitlines() if line.strip()]
        alembic_ini_path = next((line for line in lines if "alembic.ini" in line), None)

        if alembic_ini_path:
            info("Alembic configuration found!")
            return True, alembic_ini_path.strip()
        else:
            info("Alembic configuration not found, skipping migrations.")
            return False, None
