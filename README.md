# LexAlyzer

LexAlyzer will analyze a youtube video, or an entire channel with all videos and make speech statistics on who talked for how long.

# Step 0: Install deps and get environment ready

* [Install poetry](https://python-poetry.org/docs/)

```
poetry install
poetry run python main.py
```

# Step 1: Obtain YouTube Data API Key

* Go to the Google Developers Console. https://console.cloud.google.com/
* Create a new project.
* Select project
* View all products -> API Services -> Library
* Search for "YouTube Data API v3", and enable it for your project.
* Click "Manage" > "Credentials" & "Create Credentials"
* Put key into keys.py
