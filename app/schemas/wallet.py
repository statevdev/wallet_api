import uuid
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class OperationType(StrEnum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class WalletOperationRequest(BaseModel):
    operation_type: OperationType = Field(examples=[OperationType.DEPOSIT])
    amount: Decimal = Field(
        gt=0,
        max_digits=18,
        decimal_places=2,
        examples=["1000.00"],
    )


class WalletResponse(BaseModel):
    id: uuid.UUID = Field(examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"])
    balance: Decimal = Field(examples=["1000.00"])
