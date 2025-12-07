'''
Main entry point for the GitHub Action.
'''

from src.github_utils import get_input, set_failed, info
from src.pa_client import PythonAnywhereClient
from src.pa_utils import PythonAnywhereUtils
from src.frameworks import FrameworkFactory

def run():
    """Main entry point for the action execution."""
    try:
        # 1. Get Inputs
        username = get_input("username", required=True)
        api_token = get_input("api_token", required=True)
        host = get_input("host", required=True)
        domain_name = get_input("domain_name", required=False)
        framework_type = get_input("framework_type", required=False, default="django")
        django_settings = get_input("django_settings", required=False)
        envs_string = get_input("envs", required=False)

        client = PythonAnywhereClient(username, api_token, host)

        # 2. Setup Console and WebApp
        _console = PythonAnywhereUtils.setup_console(client)
        console_id = _console["id"]
        web_app = PythonAnywhereUtils.setup_web_app(client, domain_name)
        
        # 3. Upload .env file if envs are provided
        if envs_string:
            try:
                envs_dict = {}
                for line in envs_string.splitlines():
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        envs_dict[key.strip()] = value.strip()
                
                if envs_dict:
                    PythonAnywhereUtils.upload_env_file(client, console_id, web_app, envs_dict)
                else:
                    info("Input 'envs' provided, but no valid KEY=VALUE pairs found. Skipping .env file upload.")

            except Exception as e:
                set_failed(f"Error processing 'envs' input: {e}")

        # 4. Git Pull
        try:
            client.send_input_to_console(
                console_id,
                f"git -C {web_app['source_directory']} pull",
                "Checking repository status..."
            )
            
            pull_response = client.get_latest_console_output(
                console_id,
                "Git Pull completed."
            )
            
            pull_success, pull_error = PythonAnywhereUtils.check_git_pull_output(pull_response)

            if not pull_success:
                error_messages = {
                    "local_changes": f"Git pull failed: Local changes detected in {web_app['source_directory']}. Please commit, stash, or reset your changes.",
                    "untracked_files": f"Git pull failed: Untracked files detected in {web_app['source_directory']}. Please add or remove the files.",
                    "git_error": "Git pull failed: Check your repository configuration and try again."
                }
                raise Exception(error_messages.get(pull_error, "Unknown Git pull error."))
            
            info("Repository updated successfully.")

        except Exception as e:
            set_failed(e)

        # 5. Framework Commands (Django/Flask)
        info(f"Executing commands for the {framework_type.capitalize()} framework...")
        try:
            framework_executor = FrameworkFactory.create(
                framework_type,
                client,
                console_id,
                web_app,
                django_settings=django_settings
            )
            framework_executor.run_commands()

        except ValueError as e:
            set_failed(str(e))
        except Exception as e:
            raise Exception(f"Error during console commands for {framework_type.capitalize()}: {e}")

        # 6. Reload WebApp
        info(f"Reloading web app: {web_app['domain_name']}...")
        client.reload_webapp(web_app['domain_name'])

        info("Web application reloaded successfully.")

    except Exception as e:
        set_failed(str(e))

if __name__ == "__main__":
    run()
