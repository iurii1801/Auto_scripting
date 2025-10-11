#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
from datetime import date, timedelta
from pathlib import Path
from typing import List
import requests


DEFAULT_BASE_URL = os.getenv("API_BASE_URL", "http://host.docker.internal:8080")
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
ERROR_LOG = Path(os.getenv("ERROR_LOG", "/app/error.log"))
API_KEY = os.getenv("API_KEY", "").strip()


def log_error(msg: str) -> None:
    """Пишем строку об ошибке в ERROR_LOG (если можно), и продублируем в stderr."""
    try:
        ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ERROR_LOG.open("a", encoding="utf-8") as f:
            f.write(msg.rstrip() + "\n")
    except Exception:
        pass
    print(msg, file=sys.stderr)


def expand_date_arg(date_arg: str) -> List[str]:
    """
    Преобразует аргумент даты в список ISO-дат.
      - 'yesterday'  → [вчера]
      - 'last_week'  → [понедельник..воскресенье прошлой недели]
      - 'YYYY-MM-DD' → [та же дата]
    """
    if not date_arg:
        raise ValueError("Не указана дата. Используй --date YYYY-MM-DD | yesterday | last_week")

    s = date_arg.strip().lower()
    if s == "yesterday":
        return [(date.today() - timedelta(days=1)).isoformat()]
    if s == "last_week":
        today = date.today()
        start = today - timedelta(days=today.weekday() + 7)  # понедельник прошлой недели
        return [(start + timedelta(days=i)).isoformat() for i in range(7)]
    # иначе считаем это валидной ISO-датой
    return [date_arg]


def build_url(base_url: str, from_cur: str, to_cur: str, d: str) -> str:
    # PHP-сервис препода ожидает вид: /?from=MDL&to=EUR&date=YYYY-MM-DD
    sep = "" if base_url.endswith("/") else "/"
    return f"{base_url}{sep}?from={from_cur}&to={to_cur}&date={d}"


def fetch_rate(base_url: str, from_cur: str, to_cur: str, d: str, timeout: float = 10.0) -> dict:
    url = build_url(base_url, from_cur, to_cur, d)
    headers = {}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    # Если сервис отдаёт text/plain с JSON — всё равно попробуем распарсить
    try:
        return resp.json()
    except Exception as e:
        # как fallback: пробуем вручную
        return json.loads(resp.text)


def save_json(data: dict, from_cur: str, to_cur: str, d: str) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_name = f"rate_{from_cur}_{to_cur}_{d}.json"
    out_path = DATA_DIR / out_name
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def parse_args(argv: List[str]) -> argparse.Namespace:
    """
    Поддерживает как флаги (рекомендовано), так и позиционные аргументы (для совместимости):
      python3 currency_exchange_rate.py --from MDL --to EUR --date yesterday
      python3 currency_exchange_rate.py MDL EUR 2025-10-10
    """
    parser = argparse.ArgumentParser(description="Fetch currency rate and save JSON.")
    parser.add_argument("--from", dest="from_cur", help="Base currency, e.g. MDL")
    parser.add_argument("--to", dest="to_cur", help="Quote currency, e.g. EUR")
    parser.add_argument("--date", dest="date_arg", help="Date: YYYY-MM-DD | yesterday | last_week")

    # Если пользователь дал позиционные аргументы: FROM TO DATE
    # распарсим их, но только если флаги не указаны
    # Пример: currency_exchange_rate.py MDL EUR yesterday
    if len(argv) == 3 and all(a is None for a in (os.getenv("PARSE_FLAGS"),)):
        # пробуем как позиционные
        pos_from, pos_to, pos_date = argv
        ns = argparse.Namespace(from_cur=pos_from, to_cur=pos_to, date_arg=pos_date)
        return ns

    # Иначе обычный путь — флаги
    ns = parser.parse_args(argv)

    # простая валидация
    missing = []
    if not ns.from_cur:
        missing.append("--from")
    if not ns.to_cur:
        missing.append("--to")
    if not ns.date_arg:
        missing.append("--date")
    if missing:
        parser.error("Отсутствуют обязательные аргументы: " + ", ".join(missing))

    return ns


def main(argv: List[str]) -> int:
    try:
        args = parse_args(argv)
        from_cur = args.from_cur.strip().upper()
        to_cur = args.to_cur.strip().upper()
        dates = expand_date_arg(args.date_arg)

        success = True
        for d in dates:
            try:
                data = fetch_rate(DEFAULT_BASE_URL, from_cur, to_cur, d, timeout=15.0)
                out_path = save_json(data, from_cur, to_cur, d)
                print(f"Saved: {out_path}")
            except Exception as e:
                success = False
                log_error(f"{date.today().isoformat()} ERROR for {from_cur}->{to_cur} {d}: {e}")

        return 0 if success else 1

    except SystemExit:
        # argparse уже всё напечатал
        raise
    except Exception as e:
        log_error(f"{date.today().isoformat()} FATAL: {e}")
        return 1


if __name__ == "__main__":
    # argv без имени скрипта
    sys.exit(main(sys.argv[1:]))
