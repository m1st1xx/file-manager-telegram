# File Manager Telegram Bot

Telegram-бот на aiogram 3 для существующего File Manager.

## Общие данные с сайтом

Бот не создаёт отдельное хранилище файлов. Он использует:

- `new_users.db` — аккаунты и предметы;
- `users.db` — legacy-аккаунты;
- `uploads/` — файлы.

Для Docker эти же файлы можно примонтировать из `/var/private`.

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export BOT_TOKEN="..."
export NEW_DB_PATH="/path/to/new_users.db"
export OLD_DB_PATH="/path/to/users.db"
export UPLOAD_BASE="/path/to/uploads"
python bot.py
```

## Docker Compose

Добавьте сервис:

```yaml
telegram-bot:
  build: ./telegram_bot
  container_name: file-manager-telegram-bot
  env_file: .env
  restart: always
  volumes:
    - /var/private/uploads:/app/uploads
    - /var/private/users.db:/app/users.db
    - /var/private/new_users.db:/app/new_users.db
```

В `.env`:

```env
BOT_TOKEN=YOUR_BOT_TOKEN
NEW_DB_PATH=/app/new_users.db
OLD_DB_PATH=/app/users.db
UPLOAD_BASE=/app/uploads
MAX_FILE_SIZE=51380224
```

## Важно

Telegram Bot API ограничивает размер файлов, которые бот может скачать. Поэтому фактический лимит зависит также от Telegram/API.

Сессии Telegram хранятся только в памяти процесса и сбрасываются после перезапуска бота.
