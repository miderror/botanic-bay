#!/bin/bash
set -e

case "$SERVICE_TYPE" in
  telegram_bot)
    echo "Starting Telegram bot..."
    python -m app.services.telegram.run_bot
    ;;
  fastapi)
    echo "Starting FastAPI server..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-config logging.ini
    ;;
esac