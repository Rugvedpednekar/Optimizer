# Optimizer

Optimizer is a dark-theme paper trading platform built with FastAPI, server-rendered HTML, and vanilla JavaScript.

## Features

- Authentication
- Watchlist and market analysis
- Paper trading portfolio
- Backtesting
- Algo jobs
- AI chat

## Local Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

- `http://127.0.0.1:8000`

## Environment

Create a `.env` file from `.env.example`.

## Railway

This project is set up for Railway using:

- `Procfile`
- `railway.json`

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
