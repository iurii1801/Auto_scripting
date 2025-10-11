FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Chisinau

RUN apt-get update && apt-get install -y --no-install-recommends \
    cron tzdata \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости и ставим их
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt || pip install --no-cache-dir requests

# Копируем приложение и cron
COPY currency_exchange_rate.py /app/currency_exchange_rate.py
COPY cronjob /app/cronjob
COPY entrypoint.sh /entrypoint.sh

# Права
RUN chmod +x /entrypoint.sh \
 && touch /var/log/cron.log \
 && chmod 666 /var/log/cron.log

# Проверим crontab на этапе сборки
RUN crontab /app/cronjob

VOLUME ["/app/data"]

ENTRYPOINT ["/entrypoint.sh"]