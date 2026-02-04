# app/models/reconciliation.py
"""
SQLAlchemy models for the reconciliation system.
Contains Merchant, Order, and Payment models with relationships.
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


# ============== MERCHANT MODEL ==============

class Merchant(Base):
    """
    Merchant master data table.
    Stores merchant information - referenced by both orders and payments.
    """
    __tablename__ = "merchants"

    # Primary key - auto-increment integer (fast for foreign keys)
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Business identifier - what humans use to identify merchants (UNIQUE)
    merchant_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Merchant information
    merchant_name = Column(String(100), nullable=False)
    
    # Audit timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships - SQLAlchemy uses these for JOIN operations
    # "Order" and "Payment" are class names (defined below)
    # back_populates creates bidirectional relationship
    orders = relationship("Order", back_populates="merchant")
    payments = relationship("Payment", back_populates="merchant")

    def __repr__(self):
        """String representation for debugging"""
        return f"<Merchant(id={self.id}, merchant_id='{self.merchant_id}', name='{self.merchant_name}')>"
    



# ============== ORDER STATUS ENUM ==============

class OrderStatus(str, enum.Enum):
    """Status values for order lifecycle"""
    pending = "pending"          # Order created, awaiting completion
    completed = "completed"      # Order fulfilled, ready for reconciliation
    failed = "failed"           # Order cancelled or failed
    reconciled = "reconciled"   # Matched with a payment


# ============== ORDER MODEL ==============

class Order(Base):
    """
    Order records from merchants.
    These are the "expected" transactions that payments should match against.
    """
    __tablename__ = "orders"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key to merchants table
    # This creates the many-to-one relationship: many orders → one merchant
    merchant_id = Column(
        Integer, 
        ForeignKey('merchants.id'),  # References merchants.id
        nullable=False,               # Every order MUST have a merchant
        index=True                    # Index for fast filtering by merchant
    )
    
    # Order identification
    merchant_order_id = Column(
        String(100), 
        unique=True,      # Each order must have unique ID
        nullable=False,   # Required field
        index=True        # Index for fast lookups during reconciliation
    )
    
    # Order financial details
    amount = Column(Numeric(10, 2), nullable=False)      # Decimal for precise money
    currency = Column(String(3), nullable=False)         # USD, EUR, etc.
    description = Column(String(255), nullable=True)     # Optional notes
    
    # Order timing
    order_date = Column(Date, nullable=False)  # When order was created
    
    # Status tracking
    status = Column(
        Enum(OrderStatus), 
        default=OrderStatus.pending,  # New orders start as pending
        nullable=False
    )
    
    # Audit timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship back to merchant
    # This enables: order.merchant to get merchant info
    # Matches merchant.orders relationship we defined earlier
    merchant = relationship("Merchant", back_populates="orders")

    def __repr__(self):
        """String representation for debugging"""
        return f"<Order(id={self.id}, merchant_order_id='{self.merchant_order_id}', amount={self.amount}, status={self.status.value})>"
    


# ============== PAYMENT STATUS ENUM ==============

class PaymentStatus(str, enum.Enum):
    """Status values for payment lifecycle"""
    pending = "pending"          # Payment initiated, awaiting completion
    completed = "completed"      # Payment processed, ready for reconciliation
    failed = "failed"           # Payment failed or reversed
    reconciled = "reconciled"   # Matched with an order


# ============== PAYMENT MODEL ==============

class Payment(Base):
    """
    Payment records received from payment processors.
    These are the "actual" transactions that should match against orders.
    """
    __tablename__ = "payments"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key to merchants table
    # Many payments → one merchant
    merchant_id = Column(
        Integer, 
        ForeignKey('merchants.id'),  # References merchants.id
        nullable=False,               # Every payment MUST have a merchant
        index=True                    # Index for fast filtering
    )
    
    # Payment identification
    # Links this payment to an order via merchant_order_id
    merchant_order_id = Column(
        String(100), 
        unique=True,      # One-to-one: each payment references one order
        nullable=False,   # Required field
        index=True        # Index for reconciliation matching
    )
    
    # Payment financial details
    amount = Column(Numeric(10, 2), nullable=False)      # Decimal for precise money
    currency = Column(String(3), nullable=False)         # USD, EUR, etc.
    description = Column(String(255), nullable=True)     # Optional notes
    
    # Payment timing
    payment_date = Column(Date, nullable=False)  # When payment was received
    
    # Status tracking
    status = Column(
        Enum(PaymentStatus), 
        default=PaymentStatus.pending,  # New payments start as pending
        nullable=False
    )
    
    # Audit timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship back to merchant
    # This enables: payment.merchant to get merchant info
    # Matches merchant.payments relationship
    merchant = relationship("Merchant", back_populates="payments")

    def __repr__(self):
        """String representation for debugging"""
        return f"<Payment(id={self.id}, merchant_order_id='{self.merchant_order_id}', amount={self.amount}, status={self.status.value})>"