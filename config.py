import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    COMMAND_CHANNEL = int(os.getenv('CMD_CHANNEL'))
    BOT_ADMIN_ID = int(os.getenv('ADMIN_ID'))
    DB_URI = os.getenv('DB_URI')
    DB_USERNAME = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASS')