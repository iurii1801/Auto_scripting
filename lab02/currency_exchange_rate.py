#!/usr/bin/env python3
"""
currency_exchange_rate.py
Скрипт для работы с Currency Exchange API:
- Получает курс валюты на определённую дату
- Сохраняет результат в JSON
- Логирует ошибки в error.log
"""

import argparse
import json
import logging
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

import requests
from dotenv import load_dotenv

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def load_api_key(project_root: Path, cli_key: Optional[str]) -> str:
    """Берём API-ключ: CLI → ENV → .env"""
    if cli_key:
        return cli_key
    if os.getenv("API_KEY"):
        return os.environ["API_KEY"]
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        if os.getenv("API_KEY"):
            return os.environ["API_KEY"]
    raise RuntimeError("API key отсутствует. Укажите --api-key или задайте его в .env/переменной окружения")

def validate_date(date_str: str) -> str:
    if not DATE_RE.match(date_str):
        raise ValueError("Дата должна быть в формате YYYY-MM-DD")
    datetime.strptime(date_str, "%Y-%m-%d")  # проверка корректности даты
    return date_str

def ensure_dirs(project_root: Path) -> Path:
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def setup_logger(project_root: Path) -> logging.Logger:
    logger = logging.getLogger("lab02")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(project_root / "error.log", encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh.setFormatter(fmt)
    if not logger.handlers:
        logger.addHandler(fh)
    return logger

def save_json(data_dir: Path, from_cur: str, to_cur: str, date_str: str, payload: dict) -> Path:
    filename = f"rate_{from_cur.upper()}_{to_cur.upper()}_{date_str}.json"
    out_path = data_dir / filename
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return out_path

def list_currencies(base_url: str, api_key: str) -> list:
    url = f"{base_url.rstrip('/')}/?currencies"
    resp = requests.post(url, data={"key": api_key}, timeout=10)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("error"):
        raise RuntimeError(payload["error"])
    return payload.get("data", [])

def fetch_rate(base_url: str, api_key: str, from_cur: str, to_cur: str, date_str: str) -> dict:
    params = {"from": from_cur.upper(), "to": to_cur.upper(), "date": date_str}
    url = f"{base_url.rstrip('/')}/"
    resp = requests.post(url, params=params, data={"key": api_key}, timeout=10)
    resp.raise_for_status()
    return resp.json()

def main() -> int:
    parser = argparse.ArgumentParser(description="Скрипт для получения курса валюты через API")
    parser.add_argument("from_currency", help="Валюта источника (например, USD)")
    parser.add_argument("to_currency", help="Валюта назначения (например, MDL)")
    parser.add_argument("date", help="Дата в формате YYYY-MM-DD")
    parser.add_argument("--url", default="http://localhost:8080", help="Базовый URL сервиса")
    parser.add_argument("--api-key", dest="api_key", help="API ключ")
    parser.add_argument("--list-currencies", action="store_true", help="Показать список валют и выйти")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    logger = setup_logger(project_root)

    try:
        api_key = load_api_key(project_root, args.api_key)
    except Exception as e:
        print(f"Ошибка: {e}")
        logger.error(f"{e}")
        return 2

    if args.list_currencies:
        try:
            cur_list = list_currencies(args.url, api_key)
            print("Доступные валюты:", ", ".join(cur_list))
            return 0
        except Exception as e:
            print(f"Ошибка при получении списка валют: {e}")
            logger.error(f"list_currencies failed: {e}")
            return 3

    try:
        date_str = validate_date(args.date)
    except Exception as e:
        print(f"Ошибка: {e}")
        logger.error(f"Invalid date '{args.date}': {e}")
        return 2

    try:
        payload = fetch_rate(args.url, api_key, args.from_currency, args.to_currency, date_str)
    except requests.HTTPError as e:
        print(f"HTTP ошибка: {e}")
        logger.error(f"HTTP error: {e}")
        return 4
    except requests.RequestException as e:
        print(f"Ошибка сети/запроса: {e}")
        logger.error(f"Request error: {e}")
        return 5
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        logger.error(f"Unexpected: {e}")
        return 6

    if payload.get("error"):
        msg = payload["error"]
        print(f"Ошибка API: {msg}")
        logger.error(f"API error: {msg} | params: from={args.from_currency}, to={args.to_currency}, date={date_str}")
        return 1

    data = payload.get("data", {})
    data_dir = ensure_dirs(project_root)
    out_path = save_json(data_dir, args.from_currency, args.to_currency, date_str, data)
    print(f"OK. Сохранено: {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
