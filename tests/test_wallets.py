from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_create_wallet(client):
    response = client.post("/api/v1/wallets")

    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    assert data["balance"] == "0.00"


def test_get_wallet(client):
    create_response = client.post("/api/v1/wallets")
    wallet_id = create_response.json()["id"]

    response = client.get(f"/api/v1/wallets/{wallet_id}")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == wallet_id
    assert data["balance"] == "0.00"


def test_list_wallets(client):
    first_response = client.post("/api/v1/wallets")
    second_response = client.post("/api/v1/wallets")
    first_wallet_id = first_response.json()["id"]
    second_wallet_id = second_response.json()["id"]

    response = client.get("/api/v1/wallets")

    assert response.status_code == 200

    wallet_ids = {wallet["id"] for wallet in response.json()}
    assert first_wallet_id in wallet_ids
    assert second_wallet_id in wallet_ids


def test_list_wallets_with_pagination(client):
    wallet_ids = [
        client.post("/api/v1/wallets").json()["id"]
        for _ in range(3)
    ]
    sorted_wallet_ids = sorted(wallet_ids)

    response = client.get("/api/v1/wallets", params={"limit": 1, "offset": 1})

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == sorted_wallet_ids[1]


def test_deposit_wallet(client):
    create_response = client.post("/api/v1/wallets")
    wallet_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={
            "operation_type": "DEPOSIT",
            "amount": 1000,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == wallet_id
    assert data["balance"] == "1000.00"


def test_withdraw_wallet(client):
    create_response = client.post("/api/v1/wallets")
    wallet_id = create_response.json()["id"]

    client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={
            "operation_type": "DEPOSIT",
            "amount": 1000,
        },
    )

    response = client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={
            "operation_type": "WITHDRAW",
            "amount": 300,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == wallet_id
    assert data["balance"] == "700.00"


def test_withdraw_wallet_insufficient_funds(client):
    create_response = client.post("/api/v1/wallets")
    wallet_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={
            "operation_type": "WITHDRAW",
            "amount": 1000,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient funds"


def test_get_wallet_not_found(client):
    wallet_id = uuid4()

    response = client.get(f"/api/v1/wallets/{wallet_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Wallet not found"


def test_wallet_operation_with_invalid_operation_type(client):
    create_response = client.post("/api/v1/wallets")
    wallet_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={
            "operation_type": "TRANSFER",
            "amount": 1000,
        },
    )

    assert response.status_code == 422


def test_wallet_operation_with_too_many_decimal_places(client):
    create_response = client.post("/api/v1/wallets")
    wallet_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={
            "operation_type": "DEPOSIT",
            "amount": "0.009",
        },
    )

    assert response.status_code == 422


def test_wallet_operation_with_too_many_digits(client):
    create_response = client.post("/api/v1/wallets")
    wallet_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={
            "operation_type": "DEPOSIT",
            "amount": "10000000000000000.00",
        },
    )

    assert response.status_code == 422


def test_wallet_deposit_over_balance_limit(client):
    create_response = client.post("/api/v1/wallets")
    wallet_id = create_response.json()["id"]

    client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={
            "operation_type": "DEPOSIT",
            "amount": "9999999999999999.99",
        },
    )

    response = client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={
            "operation_type": "DEPOSIT",
            "amount": "0.01",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Balance limit exceeded"

    response = client.get(f"/api/v1/wallets/{wallet_id}")
    assert response.status_code == 200
    assert response.json()["balance"] == "9999999999999999.99"


def test_many_clients_withdraw_from_same_wallet(client):
    create_response = client.post("/api/v1/wallets")
    wallet_id = create_response.json()["id"]

    clients_count = 50
    initial_balance = 1000
    withdraw_amount = 100
    expected_success_count = 10
    expected_error_count = clients_count - expected_success_count
    expected_balance = "0.00"

    client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={
            "operation_type": "DEPOSIT",
            "amount": initial_balance,
        },
    )

    start = Barrier(clients_count)

    def withdraw():
        start.wait()

        with TestClient(app) as local_client:
            return local_client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={
                    "operation_type": "WITHDRAW",
                    "amount": withdraw_amount,
                },
            )

    with ThreadPoolExecutor(max_workers=clients_count) as executor:
        futures = [executor.submit(withdraw) for _ in range(clients_count)]
        responses = [future.result() for future in futures]

    statuses = [response.status_code for response in responses]
    status_counts = Counter(statuses)

    assert status_counts[200] == expected_success_count
    assert status_counts[400] == expected_error_count

    response = client.get(f"/api/v1/wallets/{wallet_id}")
    assert response.status_code == 200
    assert response.json()["balance"] == expected_balance
