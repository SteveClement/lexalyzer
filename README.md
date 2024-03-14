# LexAlyzer

LexAlyzer (lex-analyzer) is a powerful tool that analyzes YouTube videos or entire channels, providing detailed speech statistics on who spoke for how long.

## Assumptions

TBC

# Step 0: Install deps and get environment ready

* [Install poetry](https://python-poetry.org/docs/)

```
sudo apt install pipx
pipx install poetry
git clone <repo>
cd <repo>
poetry install
poetry run python main.py
```

# Step 1: Obtain YouTube Data API Key

To obtain a YouTube Data API key, follow these steps:

1. Go to the [Google Developers Console](https://console.cloud.google.com/).
2. Create a new project.
3. Select the created project.
4. Click on "View all products" > "API Services" > "Library".
5. Search for "YouTube Data API v3" and enable it for your project.
6. Click on "Manage" > "Credentials" > "Create Credentials".
7. Choose "API key" as the credential type.
8. Copy the generated API key.
9. Create a file named `keys.py` in your project directory.
10. Inside `keys.py`, add the following line of code:
    ```python
    YOUTUBE_API_KEY = "<your-api-key>"
    ```