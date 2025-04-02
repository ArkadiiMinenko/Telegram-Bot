import os
from dotenv import load_dotenv

# Determine which .env file to load
env_docker_path = os.path.join(os.getcwd(), '.env.docker')
env_default_path = os.path.join(os.getcwd(), '.env')

if os.path.exists(env_docker_path):
    load_dotenv(dotenv_path=env_docker_path)
else:
    load_dotenv(dotenv_path=env_default_path)

# Core settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///translator_bot.db")

# DB size limits
MAX_DB_SIZE_MB = int(os.getenv("MAX_DB_SIZE_MB", 400))
