import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
NEW_DB_PATH = Path(os.getenv("NEW_DB_PATH", "/app/new_users.db"))
OLD_DB_PATH = Path(os.getenv("OLD_DB_PATH", "/app/users.db"))
UPLOAD_BASE = Path(os.getenv("UPLOAD_BASE", "/app/uploads"))
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(49 * 1024 * 1024)))
