import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Access the bot token from the environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# You can add more configuration settings here as needed
DEBUG = os.getenv("DEBUG", "False").lower() == "true"  # Convert 'True'/'False' string to boolean
