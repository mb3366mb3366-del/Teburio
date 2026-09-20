# Teburio Login Automation

Playwright script that logs into https://app.teburio.de/login.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env  # then fill in TEBURIO_EMAIL and TEBURIO_PASSWORD
```

## Run

```bash
export $(cat .env | xargs)
python login.py
```
