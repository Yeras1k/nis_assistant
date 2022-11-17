import os

BOT_TOKEN = os.environ.get('BOT_TOKEN')
APP_URL = os.environ.get('APP_URL') + BOT_TOKEN
DB_URI = os.environ.get('DB_URI')
