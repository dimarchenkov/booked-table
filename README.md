# Booked Table

Production-ready сервис бронирования столов по времени с Telegram-ботом, админкой, оплатой и календарной синхронизацией.

## Быстрый старт

```bash
git clone <repo>
cd booked-table
cp .env.example .env

docker compose up --build
```

API будет доступен по `http://localhost:8000`.

## Админка

- URL: `http://localhost:8000/admin`
- Логин: `ADMIN_EMAIL`
- Пароль: соответствует `ADMIN_PASSWORD_HASH` (bcrypt hash в ENV).

Пример генерации хеша:

```bash
python - <<'PY'
import bcrypt
password = b"change-me"
print(bcrypt.hashpw(password, bcrypt.gensalt()).decode())
PY
```

## Seed данных

```bash
docker compose exec api python -m app.scripts.seed
```

Seed создаёт:
- ScheduleRule
- WorkingHours (пн-вс 09:00-21:00)
- 3 таблицы

## Проверка здоровья

```bash
curl http://localhost:8000/health
```

## Пример бронирования (curl)

1. Проверка доступности:

```bash
curl "http://localhost:8000/availability?table_id=1&date=2025-01-06"
```

2. HOLD-бронирование:

```bash
curl -X POST "http://localhost:8000/bookings/hold" \
  -H "Content-Type: application/json" \
  -d '{
    "table_id": 1,
    "start_at": "2025-01-06T09:00:00Z",
    "end_at": "2025-01-06T10:00:00Z",
    "tg_user_id": 123456,
    "name": "Alex",
    "phone": "+79000000000"
  }'
```

Ответ содержит `bookingId` и `paymentUrl`. В режиме Stub URL будет вида `http://localhost:8000/payments/{id}/stub`.

## Ручное подтверждение брони (MVP)

```bash
curl -X POST "http://localhost:8000/bookings/1/confirm" -H "X-Admin-Api-Key: $ADMIN_API_KEY"
```

## Telegram бот

Bot запускается отдельным сервисом `telegram_bot`.

- Если `TELEGRAM_BOT_TOKEN` отсутствует, бот выводит лог и завершает работу без ошибки.
- Username бота получается через `getMe()`, fallback — `TELEGRAM_BOT_USERNAME`.

Команды:
- `/start` — начать
- `/mybookings` — активные брони
- `/cancel <id>` — отменить бронь
- `/post_booking` — постер в группу (только для admin ids)

## Group poster

В админке доступна страница **Group Poster** с готовым текстом и ссылкой:

```
📦 Аренда столов для упаковки. Нажмите кнопку ниже, чтобы забронировать время.
https://t.me/<bot_username>?start=from_group
```

## Интеграции

Все интеграции включаются флагами.

### T-Bank

- `TBANK_ENABLED=false` (по умолчанию)
- При выключенном флаге webhook отвечает `501`.

### CalDAV (Яндекс)

- `CALENDAR_ENABLED=false` (по умолчанию)
- При выключенном флаге используется Stub.

## Полезные команды

```bash
make migrate
make test
```

## Архитектура

```
app/
  main.py
  api/
  admin/
  core/
  db/
  models/
  services/
  workers/
  scripts/
telegram_bot/
```
