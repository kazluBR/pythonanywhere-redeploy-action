# GitHub Action: PythonAnywhere Re-Deploy

This is a custom GitHub Action to automate the re-deployment process for Python-based web applications (Django or Flask) hosted on PythonAnywhere. The action performs a Git pull of the latest code, installs dependencies, runs database migrations (if applicable), and reloads the web application.

## Features

- **Secure Authentication:** Uses the PythonAnywhere API token for communication.
- **Automated Git Pull:** Executes `git pull` in the application's directory on PythonAnywhere.
- **Dependency Management:** Activates the virtual environment and installs dependencies via `pip install -r requirements.txt`.
- **Django Support:** Executes `python manage.py migrate`.
- **Flask/Alembic Support:** Checks for the existence of `alembic.ini` and executes `alembic upgrade head` if found.
- **Web App Reload:** Reloads the web application after deployment.
- **Custom Settings (Django):** Allows specifying a custom settings module for `manage.py` commands via the `django_settings` input.
- **Environment Variables (`.env`):** Allows passing a multi-line string environment variables (e.g., secrets) to be written to a `.env` file in the application's source directory on PythonAnywhere.

## PythonAnywhere Setup

Before using this action, make sure your PythonAnywhere account is properly configured:

1. Create an API Token

The API token is required to allow the GitHub Action to communicate with your PythonAnywhere account.

Go to Account → API token.

Click “Create a new API token” (if one doesn’t already exist).

Copy this token and store it as a GitHub secret (e.g., PA_API_TOKEN).

2. Configure SSH Access to GitHub

The action executes a git pull on your PythonAnywhere account, so SSH access must be configured:

In your PythonAnywhere bash console, run:

```bash
ssh-keygen
cat ~/.ssh/id_rsa.pub
```

Copy the key and add it to your GitHub repository under
Settings → Deploy keys → Add deploy key (check Allow write access if necessary).

3. Create a Virtual Environment

Your app should use a dedicated virtual environment for isolated dependencies.

Example:

```bash
mkvirtualenv env --python=python3.11
workon env
```

Make sure your Web App on PythonAnywhere is configured to use this virtualenv under:
Web → Virtualenv path.

4. Keep a Bash Console Open

Keep at least one Bash console open and active in your PythonAnywhere account.
This is required because the PythonAnywhere API does not actually start console processes — it can only reference existing ones.

⚠️ According to PythonAnywhere’s own [documentation](https://help.pythonanywhere.com/pages/API/#consoles):

“_Create a new console object (NB does not actually start the process. Only connecting to the console in a browser will do that)._”

In practice, this means:

- You must manually open a Bash console from the PythonAnywhere Dashboard → Consoles → Start a new console → Bash.

- The console process must stay active (do not close it).

## Usage

To use this action in your GitHub Actions workflow, add a step like the following:

```yaml
name: Deploy to PythonAnywhere

on:
  push:
    branches:
      - master

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Re-Deploy WebApp on PythonAnywhere
        uses: kazluBR/pythonanywhere-redeploy-action@v1.0.0
        with:
          host: "www.pythonanywhere.com"                        # Required
          username: ${{ secrets.PA_USERNAME }}                  # Required
          api_token: ${{ secrets.PA_API_TOKEN }}                # Required
          domain_name: your-application.pythonanywhere.com      # Optional, gets first webapp
          framework_type: "django" or "flask"                   # Optional, defaults to django
          django_settings: "my_project.settings.production"     # Optional
          envs: |                                               # Optional, multi-line string of environment variables
            DJANGO_SECRET_KEY=${{ secrets.DJANGO_SECRET_KEY }}
            DATABASE_USERNAME=${{ secrets.DATABASE_USERNAME }}
            DATABASE_PASSWORD=${{ secrets.DATABASE_PASSWORD }}
```

## Inputs

| Name              | Description                                                                                                                                                                                                      | Required | Default                  |
| :---------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------- | :----------------------- |
| `host`            | PythonAnywhere host (EU/US), e.g., `eu.pythonanywhere.com` or `www.pythonanywhere.com`.                                                                                                                          | Yes      |                          |
| `username`        | PythonAnywhere username.                                                                                                                                                                                         | Yes      |                          |
| `api_token`       | PythonAnywhere API token.                                                                                                                                                                                        | Yes      |                          |
| `domain_name`     | Domain name of the web app to be reloaded.                                                                                                                                                                       | No       | The first web app found. |
| `framework_type`  | Application framework type.                                                                                                                                                                                      | No       | `django`                 |
| `django_settings` | Custom Django settings module to be used for `manage.py` commands (e.g., `manage.py migrate --settings=...`).                                                                                                    | No       |                          |
| `envs`            | Multi-line string of environment variables (KEY=VALUE) to be written to a `.env` file in the application's source directory on PythonAnywhere. **Use the `env` context or a multi-line string to pass secrets.** | No       |                          |
