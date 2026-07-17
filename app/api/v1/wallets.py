import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.wallet import Wallet
from app.schemas.wallet import OperationType, WalletOperationRequest, WalletResponse

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("", response_model=WalletResponse, status_code=201)
def create_wallet(db: Session = Depends(get_db)):
    wallet = Wallet()

    db.add(wallet)
    db.commit()
    db.refresh(wallet)

    return wallet


@router.get("/{wallet_id}", response_model=WalletResponse)
def get_wallet(wallet_id: uuid.UUID, db: Session = Depends(get_db)):
    wallet = db.get(Wallet, wallet_id)

    if wallet is None:
        raise HTTPException(status_code=404, detail="Wallet not found")

    return wallet


@router.post("/{wallet_id}/operation", response_model=WalletResponse)
def operate_wallet(wallet_id: uuid.UUID, operation: WalletOperationRequest, db: Session = Depends(get_db)):
    wallet = db.execute(select(Wallet).where(Wallet.id == wallet_id).with_for_update()).scalar_one_or_none()

    if wallet is None:
        raise HTTPException(status_code=404, detail="Wallet not found")

    if operation.operation_type == OperationType.DEPOSIT:
        wallet.balance += operation.amount
    elif operation.operation_type == OperationType.WITHDRAW:
        if wallet.balance < operation.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")

        wallet.balance -= operation.amount

    db.commit()
    db.refresh(wallet)

    return wallet
