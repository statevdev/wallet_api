# Wallet API

[![CI](https://github.com/statevdev/wallet_api/actions/workflows/ci.yml/badge.svg)](https://github.com/statevdev/wallet_api/actions/workflows/ci.yml)

REST API для управления кошельками: создание кошелька, получение баланса и изменение баланса через операции пополнения и списания.

## Стек

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pytest
- Ruff
- Docker Compose

## Запуск проекта

Запустить приложение и базу данных:

```bash
docker compose up --build
```

API будет доступно по адресу:

```text
http://localhost:8000
```

Swagger-документация:

```text
http://localhost:8000/docs
```

## Эндпойнты

Создать кошелек:

```http
POST /api/v1/wallets
```

Получить список кошельков:

```http
GET /api/v1/wallets?limit=100&offset=0
```

Поддерживается пагинация через `limit` и `offset`. `limit` принимает значения от `1` до `100`, `offset` — от `0`.

Получить баланс кошелька:

```http
GET /api/v1/wallets/{wallet_id}
```

Изменить баланс кошелька:

```http
POST /api/v1/wallets/{wallet_id}/operation
```

Пример тела запроса:

```json
{
  "operation_type": "DEPOSIT",
  "amount": 1000
}
```

Допустимые операции:

```text
DEPOSIT
WITHDRAW
```

## Тесты

Запустить тесты:

```bash
docker compose exec app pytest
```

Запустить Ruff:

```bash
docker compose exec app ruff check .
```

## Конкурентность

Операции изменения баланса используют блокировку строки в PostgreSQL через `SELECT ... FOR UPDATE`.

Это защищает кошелек от race condition при параллельных запросах на изменение баланса одного и того же кошелька.

## Ограничения (TODO)

API не содержит аутентификацию и авторизацию: в рамках тестового задания кошельки не привязаны к пользователям, поэтому любой клиент, имеющий доступ к API, может обратиться к любому кошельку по UUID.

Операции изменения баланса не являются идемпотентными: повторный `POST /operation` повторно изменит баланс. Например, если сервер успешно зачислил деньги, но клиент не получил ответ из-за сетевого сбоя и повторил запрос, сумма будет зачислена второй раз. Для production-версии стоит добавить `operation_id` и хранить выполненные операции в отдельной таблице с уникальным ограничением.

## CI

В GitHub Actions настроен workflow, который при `push` запускает:

- установку зависимостей;
- проверку кода через Ruff;
- тесты через Pytest.
