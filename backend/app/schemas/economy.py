import uuid
from datetime import datetime
from pydantic import BaseModel


class WalletStatus(BaseModel):
    fiat: int
    crypto: int
    privacy_coin: int
    reputation: int


class TransactionRecord(BaseModel):
    id: uuid.UUID
    amount: int
    currency: str
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MarketListingSchema(BaseModel):
    id: uuid.UUID
    item_type: str
    item_name: str
    description: str
    price_crypto: int
    quantity: int
    seller_handle: str
    expires_at: datetime | None
    effect_data: dict

    model_config = {"from_attributes": True}


class PurchaseRequest(BaseModel):
    listing_id: uuid.UUID
    quantity: int = 1


class LaunderingStep(BaseModel):
    step_number: int
    from_currency: str
    to_currency: str
    amount_in: int
    fee_percentage: float
    fee_amount: int
    amount_out: int
    heat_generated: int


class LaunderingChain(BaseModel):
    steps: list[LaunderingStep]
    total_input: int
    total_output: int
    total_fees: int
    total_heat: int
    skill_level: int
