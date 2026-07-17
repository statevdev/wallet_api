import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.wallet import Wallet
from app.schemas.wallet import OperationType, WalletOperationRequest, WalletResponse

router = APIRouter(prefix="/wallets", tags=["wallets"])

MAX_WALLET_BALANCE = Decimal("9999999999999999.99")
DEFAULT_PAGE_LIMIT = 100


@router.post("", response_model=WalletResponse, status_code=201)
def create_wallet(db: Session = Depends(get_db)):
    wallet = Wallet()

    db.add(wallet)
    db.commit()
    db.refresh(wallet)

    return wallet


@router.get("", response_model=list[WalletResponse])
def list_wallets(
    limit: int = Query(default=DEFAULT_PAGE_LIMIT, ge=1, le=DEFAULT_PAGE_LIMIT),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Wallet)
        .order_by(Wallet.id)
        .offset(offset)
        .limit(limit)
    ).all()


@router.get("/{wallet_id}", response_model=WalletResponse)
def get_wallet(wallet_id: uuid.UUID, db: Session = Depends(get_db)):
    wallet = db.get(Wallet, wallet_id)

    if wallet is None:
        raise HTTPException(status_code=404, detail="Wallet not found")

    return wallet


@router.post("/{wallet_id}/operation", response_model=WalletResponse)
def operate_wallet(wallet_id: uuid.UUID, operation: WalletOperationRequest, db: Session = Depends(get_db)):
    wallet = db.execute(
        select(Wallet)
        .where(Wallet.id == wallet_id)
        .with_for_update()
    ).scalar_one_or_none()

    if wallet is None:
        raise HTTPException(status_code=404, detail="Wallet not found")

    if operation.operation_type == OperationType.DEPOSIT:
        new_balance = wallet.balance + operation.amount

        if new_balance > MAX_WALLET_BALANCE:
            raise HTTPException(status_code=400, detail="Balance limit exceeded")

        wallet.balance += operation.amount
    elif operation.operation_type == OperationType.WITHDRAW:
        if wallet.balance < operation.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")

        wallet.balance -= operation.amount

    db.commit()
    db.refresh(wallet)

    return wallet
