# app/schemas/order.py
"""
Pydantic schemas for Order API endpoints.
Handles validation for creating orders and formatting responses.
"""

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional
from app.models.db_schema import OrderStatus


class OrderCreate(BaseModel):
    """
    Schema for creating a new order.
    User sends this in POST /orders request.
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
        description="Unique order reference from merchant"
    )
    amount: float = Field(
        ...,
        gt=0,
        description="Order amount (must be positive)"
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
        description="Optional order description"
    )
    order_date: date = Field(
        ...,
        description="Date when order was created"
    )
    status: OrderStatus = Field(
        default=OrderStatus.pending,
        description="Order status"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "merchant_id": "MERCHANT_A",
                "merchant_order_id": "ORDER_001",
                "amount": 100.00,
                "currency": "USD",
                "description": "Customer order for product XYZ",
                "order_date": "2025-01-29",
                "status": "pending"
            }
        }


class OrderResponse(BaseModel):
    """
    Schema for order responses.
    What API returns after creating or retrieving an order.
    """
    id: int
    merchant_id: int  # Database FK (integer)
    merchant_order_id: str
    amount: float
    currency: str
    description: Optional[str]
    order_date: date
    status: OrderStatus
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
                "description": "Customer order for product XYZ",
                "order_date": "2025-01-29",
                "status": "completed",
                "created_at": "2025-01-29T10:00:00",
                "updated_at": "2025-01-29T10:00:00"
            }
        }