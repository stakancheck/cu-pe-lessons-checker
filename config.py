import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot token from environment variable
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Admin Telegram IDs (comma-separated in .env)
ADMINS = [int(admin_id) for admin_id in os.getenv('ADMINS', '').split(',') if admin_id]

# Database path
DB_PATH = 'students.db'

# Available flows
FLOWS = ['Север', 'Юг', 'Запад', 'Восток']

# Required visits for credit
REQUIRED_VISITS = 5 