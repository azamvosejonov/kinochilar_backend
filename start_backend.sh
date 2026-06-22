#!/bin/bash
# Kinochilar Backend — Production ishga tushirish
# Ishlatish:  ./start_backend.sh          (development)
#             ./start_backend.sh prod     (production)

MODE="${1:-dev}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8080}"

echo "Kinochilar Backend ($MODE rejimda)"

# Virtual environment
if [ ! -d "venv" ]; then
    echo "Virtual environment yaratilmoqda..."
    python3 -m venv venv
fi
source venv/bin/activate

# Dependencies
pip install -q -r requirements.txt
pip install -q gunicorn 2>/dev/null || true

# Upload directories
mkdir -p uploads/{videos,posters,backdrops}

# Seed data (agar DB bo'sh bo'lsa)
python3 -c "
import sqlite3, os
db = os.getenv('DATABASE_URL','').replace('sqlite+aiosqlite:///','')
if db and os.path.exists(db):
    c = sqlite3.connect(db).cursor()
    c.execute(\"SELECT COUNT(*) FROM movie\")
    if c.fetchone()[0] == 0:
        print('DB bo\\'sh, seed ishga tushirilmoqda...')
        import sys; sys.exit(1)
    print(f'Kinolar soni: {c.fetchone()[0]}')
" 2>/dev/null && python3 seed.py 2>/dev/null; python3 dummy_data.py 2>/dev/null

# Start server
if [ "$MODE" = "prod" ]; then
    echo "Production: Gunicorn + Uvicorn ($PORT)"
    gunicorn app.main:app \
        -k uvicorn.workers.UvicornWorker \
        -w 4 \
        -b "$HOST:$PORT" \
        --access-logfile - \
        --error-logfile -
else
    echo "Development: Uvicorn reload ($PORT)"
    uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
fi
