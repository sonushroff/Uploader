#🇳‌🇮‌🇰‌🇭‌🇮‌🇱‌
# Add your details here and then deploy by clicking on HEROKU Deploy button
import os
from os import environ

API_ID = int(environ.get("API_ID", "26271673"))
API_HASH = environ.get("API_HASH", "0e807111856890e4770b3e5a3324ec5f")
BOT_TOKEN = environ.get("BOT_TOKEN", "8317559239:AAF0SuuW_IDKbLcqOIHITyyNTXHKQM896MQ")

OWNER = int(environ.get("OWNER", "820017857"))
CREDIT = environ.get("CREDIT", "SONU SHROFF")
cookies_file_path = os.getenv("cookies_file_path", "youtube_cookies.txt")

TOTAL_USER = os.environ.get('TOTAL_USERS', '820017857').split(',')
TOTAL_USERS = [int(user_id) for user_id in TOTAL_USER]

AUTH_USER = os.environ.get('AUTH_USERS', '820017857').split(',')
AUTH_USERS = [int(user_id) for user_id in AUTH_USER]
if int(OWNER) not in AUTH_USERS:
    AUTH_USERS.append(int(OWNER))


