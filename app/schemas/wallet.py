import uuid
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class OperationType(StrEnum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class WalletOperationRequest(BaseModel):
    operation_type: OperationType
    amount: Decimal = Field(gt=0)


class WalletResponse(BaseModel):
    id: uuid.UUID
    balance: Decimal

    model_config = {
        "from_attributes": True,
    }
