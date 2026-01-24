# Booked Table

Production-ready сервис бронирования столов по времени с оплатой T-Bank, синхронизацией CalDAV (Яндекс) и веб-админкой.

## Запуск

```bash
git clone <repo>
cd booked-table
cp .env.example .env
# заполните ENV

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

## Настройка столов и расписания

1. Войдите в админку.
2. Создайте столы в разделе `Tables`.
3. Установите глобальные правила в `ScheduleRule` (должна быть одна запись).
4. Заполните `WorkingHours` для каждого дня недели.
5. При необходимости добавьте `Closures` для закрытия всего зала или конкретного стола.

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

Ответ содержит `bookingId` и `paymentUrl` для оплаты.

## T-Bank webhook

Укажите `TBANK_NOTIFICATION_URL`, например:

```
https://<your-domain>/webhooks/tbank
```

Вебхук идемпотентен: повторные уведомления не ломают состояние.

## CalDAV (Яндекс)

- `YANDEX_LOGIN` — логин Яндекс.
- `YANDEX_APP_PASSWORD` — пароль приложения.
- `YANDEX_CALENDAR_URL` — https://caldav.yandex.ru.

По умолчанию используется первый календарь. Чтобы закрепить отдельный календарь за столом, задайте `YANDEX_CALENDAR_MAPPING` как JSON, например:

```json
{"1": "https://caldav.yandex.ru/calendars/user/calendar-id/"}
```

## Тесты

```bash
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
  tests/
```

## Полезные команды

```bash
make migrate
make test
```
