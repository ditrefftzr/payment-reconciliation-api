# app/schemas/merchant.py
"""
Pydantic schemas for Merchant API endpoints.
Handles validation for creating merchants and formatting responses.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class MerchantCreate(BaseModel):
    """
    Schema for creating a new merchant.
    This is what the user sends in POST /merchants request.
    """
    merchant_id: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Unique business identifier (e.g., 'MERCHANT_A')"
    )
    merchant_name: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Display name for the merchant"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "merchant_id": "MERCHANT_A",
                "merchant_name": "Amazon"
            }
        }


class MerchantResponse(BaseModel):
    """
    Schema for merchant responses.
    This is what the API returns after creating or retrieving a merchant.
    """
    id: int
    merchant_id: str
    merchant_name: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Allows Pydantic to read from SQLAlchemy models
        json_schema_extra = {
            "example": {
                "id": 1,
                "merchant_id": "MERCHANT_A",
                "merchant_name": "Amazon",
                "created_at": "2025-01-31T12:00:00",
                "updated_at": "2025-01-31T12:00:00"
            }
        }