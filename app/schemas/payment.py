# app/schemas/payment.py
"""
Pydantic schemas for Payment API endpoints.
Handles validation for creating payments and formatting responses.
"""

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional
from app.models.db_schema import PaymentStatus


class PaymentCreate(BaseModel):
    """
    Schema for creating a new payment.
    User sends this in POST /payments request.
    """
    merchant_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Merchant business identifier (not database id)"
    )
    merchant_order_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Order reference this payment is for"
    )
    amount: float = Field(
        ...,
        gt=0,
        description="Payment amount (must be positive)"
    )
    currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Currency code (e.g., USD)"
    )
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional payment description"
    )
    payment_date: date = Field(
        ...,
        description="Date when payment was received"
    )
    status: PaymentStatus = Field(
        default=PaymentStatus.pending,
        description="Payment status"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "merchant_id": "MERCHANT_A",
                "merchant_order_id": "ORDER_001",
                "amount": 100.00,
                "currency": "USD",
                "description": "Payment received via credit card",
                "payment_date": "2025-01-30",
                "status": "pending"
            }
        }


class PaymentResponse(BaseModel):
    """
    Schema for payment responses.
    What API returns after creating or retrieving a payment.
    """
    id: int
    merchant_id: int  # Database FK (integer)
    merchant_order_id: str
    amount: float
    currency: str
    description: Optional[str]
    payment_date: date
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "merchant_id": 1,
                "merchant_order_id": "ORDER_001",
                "amount": 100.00,
                "currency": "USD",
                "description": "Payment received via credit card",
                "payment_date": "2025-01-30",
                "status": "completed",
                "created_at": "2025-01-30T14:30:00",
                "updated_at": "2025-01-30T14:30:00"
            }
        }