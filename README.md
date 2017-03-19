# Strength program generator

A flask based generator for creating dynamic workout programs.

Requirements:

* Python 3.X (*tested on Python 3.5*)

## Local setup

Create a virtual environment using CMD:
```bash
cd /app/location/
virtualenv venv
venv/Scripts/activate.bat
pip install -r requirements.txt
```

Run the app locally by running the command `python run.py`

## Deploy on heroku

Make sure you have installed Heroku CLI and run the following:

```bash
heroku create <Optional Name> --buildpack heroku/python
heroku addons:add heroku-postgresql:hobby-dev
git push heroku master
```

# Credits

All credits goes to Tommy Odland for creating this application.
