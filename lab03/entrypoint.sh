#!/bin/sh
set -eu

create_log_file() {
  echo "Creating /var/log/cron.log ..."
  touch /var/log/cron.log
  chmod 666 /var/log/cron.log
}

install_cron() {
  echo "Installing crontab from /app/cronjob ..."
  crontab /app/cronjob
}

export_env() {
  echo "Exporting environment for cron -> /etc/environment"
  env > /etc/environment
  # маскируем ключ в выводе
  sed -E 's/(API_KEY=).*/\1****/g' /etc/environment || true
}

tail_logs() {
  echo "=== Tailing /var/log/cron.log ==="
  tail -f /var/log/cron.log &
}

start_cron() {
  echo "=== Starting cron in foreground ==="
  exec cron -f
}

create_log_file
export_env
install_cron
tail_logs
start_cron