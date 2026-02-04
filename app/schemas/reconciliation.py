# app/schemas/reconciliation.py
"""
Pydantic schemas for reconciliation responses
"""
from pydantic import BaseModel
from typing import List
from app.schemas.order import OrderResponse
from app.schemas.payment import PaymentResponse

class MatchedPair(BaseModel):
    """A matched order-payment pair"""
    order_id: int
    payment_id: int
    merchant_order_id: str
    amount: float
    
class ReconciliationResult(BaseModel):
    """Results of reconciliation process"""
    matched_count: int
    matched_pairs: List[MatchedPair]
    unmatched_orders: List[str]  # merchant_order_ids of orders with no payment
    unmatched_payments: List[str]  # merchant_order_ids of payments with no order


class ReconciliationReport(BaseModel):
    """Summary statistics for reconciliation status"""
    # Overall reconciliation metrics
    total_reconciled_amount: float
    total_reconciled_count: int
    
    # Unmatched transactions
    total_unmatched_orders: int
    total_unmatched_payments: int
    unmatched_orders_amount: float
    unmatched_payments_amount: float
    
    # Per-merchant breakdown
    merchants_summary: List[dict]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_reconciled_amount": 1500.50,
                "total_reconciled_count": 10,
                "total_unmatched_orders": 3,
                "total_unmatched_payments": 2,
                "unmatched_orders_amount": 450.00,
                "unmatched_payments_amount": 300.25,
                "merchants_summary": [
                    {
                        "merchant_id": 1,
                        "reconciled_count": 5,
                        "reconciled_amount": 750.00,
                        "unmatched_orders": 1,
                        "unmatched_payments": 0
                    }
                ]
            }
        }


class DiscrepanciesResponse(BaseModel):
    """Detailed list of unmatched transactions"""
    unmatched_orders: List['OrderResponse']
    unmatched_payments: List['PaymentResponse']