# app/main.py
"""
Payment Reconciliation API - Main application file
Three-table structure: Merchants, Orders, Payments
"""

from fastapi import FastAPI, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

# Database session dependency
from app.database import get_db

# SQLAlchemy models (database tables)
from app.models.db_schema import (
    Merchant, Order, Payment, 
    OrderStatus, PaymentStatus
)

# Pydantic schemas (API validation/responses)
from app.schemas.merchant import MerchantCreate, MerchantResponse
from app.schemas.order import OrderCreate, OrderResponse
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.schemas.reconciliation import (
    ReconciliationResult, 
    MatchedPair, 
    ReconciliationReport, 
    DiscrepanciesResponse
)

# Logging
from app.logger import logger


# Create FastAPI application
app = FastAPI(
    title="Payment Reconciliation API",
    description="API for managing merchants, orders, payments and reconciliation",
    version="2.0.0"  # Changed from 1.0.0
)


# ============== API ENDPOINTS ==============

@app.get("/")
def read_root():
    """Health check endpoint"""
    logger.info("Health check endpoint called")
    return {
        "message": "Payment Reconciliation API is running",
        "version": "2.0.0",
        "database": "MySQL (connected)"
    }


# ============== MERCHANT ENDPOINTS ==============

@app.post("/merchants", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED)
def create_merchant(
    merchant: MerchantCreate,
    db: Session = Depends(get_db)
):
    """Create a new merchant"""
    # Log what we're trying to do
    logger.info(f"Attempting to create merchant: merchant_id={merchant.merchant_id}, name={merchant.merchant_name}")
    
    try:
        # Check if merchant already exists
        existing = db.query(Merchant).filter(
            Merchant.merchant_id == merchant.merchant_id
        ).first()
        
        if existing:
            # Log the duplicate attempt
            logger.warning(f"Duplicate merchant creation attempted: {merchant.merchant_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Merchant '{merchant.merchant_id}' already exists"
            )
        
        # Create merchant
        db_merchant = Merchant(
            merchant_id=merchant.merchant_id,
            merchant_name=merchant.merchant_name,
        )
        
        db.add(db_merchant)
        db.commit()
        db.refresh(db_merchant)
        
        # Log success with the database ID
        logger.info(f"Merchant created successfully: id={db_merchant.id}, merchant_id={db_merchant.merchant_id}")
        
        return db_merchant
        
    except HTTPException:
        # Re-raise HTTPException (our duplicate error)
        raise
        
    except Exception as e:
        # Log unexpected errors
        db.rollback()
        logger.error(f"Unexpected error creating merchant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@app.get("/merchants", response_model=List[MerchantResponse])
def get_merchants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve all merchants with pagination.
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    merchants = db.query(Merchant).offset(skip).limit(limit).all()
    return merchants


@app.get("/merchants/{merchant_id}", response_model=MerchantResponse)
def get_merchant(
    merchant_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific merchant by database ID.
    
    - **merchant_id**: The database ID of the merchant
    """
    merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
    
    if merchant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant with id {merchant_id} not found"
        )
    
    return merchant



# ============== ORDER ENDPOINTS ==============

@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new order.
    - **merchant_id**: Business identifier (e.g., "MERCHANT_A")
    - **merchant_order_id**: Unique order reference
    - **amount**: Order amount (must be positive)
    - **currency**: 3-letter currency code
    - **order_date**: Date when order was created
    """
    logger.info(f"Attempting to create Order: order_id={order.merchant_order_id}, merchant_id={order.merchant_id}"
    )
    

    # Step 1: Look up merchant by business identifier
    merchant = db.query(Merchant).filter(
        Merchant.merchant_id == order.merchant_id
    ).first()
    

    if merchant is None:
        logger.warning(f"Merchant not found: {order.merchant_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant with merchant_id '{order.merchant_id}' not found"
        )
    
    # Step 2: Create new order with merchant's database ID
    db_order = Order(
        merchant_id=merchant.id,  # Use database ID (FK)
        merchant_order_id=order.merchant_order_id,
        amount=order.amount,
        currency=order.currency,
        description=order.description,
        order_date=order.order_date,
        status=order.status
    )
    
    # Step 3: Try to save - catch database integrity errors
    try:
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        logger.info(f"Order created successfully: id={db_order.id}, merchant_order_id={db_order.merchant_order_id}")
        return db_order
    except IntegrityError as e:
        db.rollback()  # Important: rollback the failed transaction
        # Check if it's a duplicate merchant_order_id error
        if "merchant_order_id" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order with merchant_order_id '{order.merchant_order_id}' already exists"
            )
        # Some other integrity error (shouldn't happen, but handle it)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database constraint violation"
        )
    
    except Exception as e:
        # Log unexpected errors
        db.rollback()
        logger.error(f"Unexpected error creating order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
    


@app.get("/orders", response_model=List[OrderResponse])
def get_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[OrderStatus] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve all orders with optional filtering.
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **merchant_id**: Filter by merchant business ID (optional)
    - **status**: Filter by order status (optional)
    """
    query = db.query(Order)
    
    
    # Filter by status if provided
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.offset(skip).limit(limit).all()
    return orders


@app.get("/orders/{merchant_order_id}", response_model=OrderResponse)
def get_order(
    merchant_order_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific order by merchant order ID.
    
    - **merchant_order_id**: The unique order reference (e.g., "ORDER_001")
    """
    order = db.query(Order).filter(
        Order.merchant_order_id == merchant_order_id
    ).first()
    
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with merchant_order_id '{merchant_order_id}' not found"
        )
    
    return order


# ============== PAYMENT ENDPOINTS ==============

@app.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new payment.
    
    - **merchant_id**: Business identifier (e.g., "MERCHANT_A")
    - **merchant_order_id**: Order reference this payment is for
    - **amount**: Payment amount (must be positive)
    - **currency**: 3-letter currency code
    - **payment_date**: Date when payment was received
    """
    logger.info(f"Attempting to create payment: merchant_order_id={payment.merchant_order_id}, merchant_id={payment.merchant_id}")
    
    # Step 1: Look up merchant by business identifier
    merchant = db.query(Merchant).filter(
        Merchant.merchant_id == payment.merchant_id
    ).first()
    
    if merchant is None:
        logger.warning(f"Merchant not found: {payment.merchant_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant with merchant_id '{payment.merchant_id}' not found"
        )
    
    # Step 2: Create new payment with merchant's database ID
    db_payment = Payment(
        merchant_id=merchant.id,
        merchant_order_id=payment.merchant_order_id,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        payment_date=payment.payment_date,
        status=payment.status
    )
    
    # Step 3: Try to save - catch database integrity errors
    try:
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        logger.info(f"Payment created successfully: id={db_payment.id}, merchant_order_id={db_payment.merchant_order_id}")
        return db_payment
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating payment: {str(e.orig)}")
        if "merchant_order_id" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment with merchant_order_id '{payment.merchant_order_id}' already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database constraint violation"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.get("/payments", response_model=List[PaymentResponse])
def get_payments(
    skip: int = 0,
    limit: int = 100,
    status: Optional[PaymentStatus] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve all payments with optional filtering.
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **status**: Filter by payment status (optional)
    """
    query = db.query(Payment)
    
    if status:
        query = query.filter(Payment.status == status)
    
    payments = query.offset(skip).limit(limit).all()
    return payments


@app.get("/payments/{merchant_order_id}", response_model=PaymentResponse)
def get_payment(
    merchant_order_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific payment by merchant order ID.
    
    - **merchant_order_id**: The order reference (e.g., "ORDER_001")
    """
    payment = db.query(Payment).filter(
        Payment.merchant_order_id == merchant_order_id
    ).first()
    
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with merchant_order_id '{merchant_order_id}' not found"
        )
    
    return payment

# ============== RECONCILIATION ENDPOINTS ==============

@app.post("/reconciliation", response_model=ReconciliationResult)
def reconcile_transactions(db: Session = Depends(get_db)):
    """
    Reconcile orders with payments using matching algorithm.
    
    Matching rules:
    1. Same merchant_order_id
    2. Same merchant_id (FK must match)
    3. Exact amount match
    4. Payment date within ±3 days of order date
    5. Both must have status='completed'
    
    Updates matched pairs to status='reconciled'
    """
    logger.info("Starting reconciliation process")
    
    try:
        # Query 1: Get all completed orders that aren't reconciled yet
        orders = db.query(Order).filter(
            Order.status == OrderStatus.completed
        ).all()
        
        logger.info(f"Found {len(orders)} completed orders to reconcile")
        
        # Query 2: Get all completed payments that aren't reconciled yet
        payments = db.query(Payment).filter(
            Payment.status == PaymentStatus.completed
        ).all()
        
        logger.info(f"Found {len(payments)} completed payments to reconcile")
        
        # Track what we've matched (prevent duplicate matching)
        matched_pairs = []
        matched_order_ids = set()
        matched_payment_ids = set()
        
        # Matching algorithm - for each order, find matching payment
        for order in orders:
            for payment in payments:
                # Skip if payment already matched (one-to-one matching)
                if payment.id in matched_payment_ids:
                    continue
                
                # Rule 1 & 2: Same merchant_order_id AND same merchant_id (FK)
                if (payment.merchant_order_id != order.merchant_order_id or 
                    payment.merchant_id != order.merchant_id):
                    continue
                
                # Rule 3: Exact amount match
                if payment.amount != order.amount:
                    logger.warning(
                        f"Amount mismatch for order {order.merchant_order_id}: "
                        f"order={order.amount}, payment={payment.amount}"
                    )
                    continue
                
                # Rule 4: Date within ±3 days (if both have dates)
                if order.order_date and payment.payment_date:
                    date_diff = abs((payment.payment_date - order.order_date).days)
                    if date_diff > 3:
                        logger.warning(
                            f"Date mismatch for order {order.merchant_order_id}: "
                            f"difference={date_diff} days (exceeds 3-day threshold)"
                        )
                        continue
                
                # MATCH FOUND! Update both to reconciled status
                order.status = OrderStatus.reconciled
                payment.status = PaymentStatus.reconciled
                
                logger.info(
                    f"Match found: order_id={order.id}, payment_id={payment.id}, "
                    f"merchant_order_id={order.merchant_order_id}, amount={order.amount}"
                )
                
                # Record the match
                matched_pairs.append(MatchedPair(
                    order_id=order.id,
                    payment_id=payment.id,
                    merchant_order_id=order.merchant_order_id,
                    amount=float(order.amount)
                ))
                
                matched_order_ids.add(order.id)
                matched_payment_ids.add(payment.id)
                break  # Move to next order (one-to-one matching)
        
        # Commit all status updates to database
        db.commit()
        
        # Find unmatched transactions
        unmatched_orders = [o.merchant_order_id for o in orders if o.id not in matched_order_ids]
        unmatched_payments = [p.merchant_order_id for p in payments if p.id not in matched_payment_ids]
        
        logger.info(
            f"Reconciliation complete: {len(matched_pairs)} matches found, "
            f"{len(unmatched_orders)} unmatched orders, {len(unmatched_payments)} unmatched payments"
        )
        
        return ReconciliationResult(
            matched_count=len(matched_pairs),
            matched_pairs=matched_pairs,
            unmatched_orders=unmatched_orders,
            unmatched_payments=unmatched_payments
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Reconciliation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during reconciliation"
        )

@app.get("/reconciliation/report", response_model=ReconciliationReport)
def get_reconciliation_report(db: Session = Depends(get_db)):
    """
    Get summary statistics for reconciliation status.
    
    Returns:
    - Total reconciled transactions (count and amount)
    - Total unmatched orders and payments
    - Breakdown by merchant
    """
    logger.info("Generating reconciliation report")
    
    try:
        # Query 1: Calculate total reconciled amount and count (PAYMENTS only)
        reconciled_stats = db.query(
            func.count(Payment.id).label('count'),
            func.sum(Payment.amount).label('total')
        ).filter(
            Payment.status == PaymentStatus.reconciled
        ).first()
        
        # Handle None case (no reconciled transactions exist)
        reconciled_count = reconciled_stats.count or 0
        reconciled_amount = float(reconciled_stats.total or 0)
        
        logger.info(f"Reconciled transactions: count={reconciled_count}, total_amount=${reconciled_amount:.2f}")
        
        # Query 2: Count unmatched ORDERS (completed but not reconciled)
        unmatched_orders_stats = db.query(
            func.count(Order.id).label('count'),
            func.sum(Order.amount).label('total')
        ).filter(
            Order.status == OrderStatus.completed
        ).first()
        
        unmatched_orders_count = unmatched_orders_stats.count or 0
        unmatched_orders_amount = float(unmatched_orders_stats.total or 0)

        # Query 3: Count unmatched PAYMENTS (completed but not reconciled)
        unmatched_payments_stats = db.query(
            func.count(Payment.id).label('count'),
            func.sum(Payment.amount).label('total')
        ).filter(
            Payment.status == PaymentStatus.completed
        ).first()
        
        unmatched_payments_count = unmatched_payments_stats.count or 0
        unmatched_payments_amount = float(unmatched_payments_stats.total or 0)
        
        logger.info(
            f"Unmatched transactions: orders={unmatched_orders_count} (${unmatched_orders_amount:.2f}), "
            f"payments={unmatched_payments_count} (${unmatched_payments_amount:.2f})"
        )

        # Query 4: Reconciled amounts by merchant (GROUP BY)
        reconciled_by_merchant = db.query(
            Payment.merchant_id,
            func.count(Payment.id).label('count'),
            func.sum(Payment.amount).label('amount')
        ).filter(
            Payment.status == PaymentStatus.reconciled,
            Payment.merchant_id.isnot(None)
        ).group_by(Payment.merchant_id).all()

        # Query 5: Unmatched orders per merchant (GROUP BY)
        unmatched_orders_by_merchant = db.query(
            Order.merchant_id,
            func.count(Order.id).label('count')
        ).filter(
            Order.status == OrderStatus.completed,
            Order.merchant_id.isnot(None)
        ).group_by(Order.merchant_id).all()

        # Query 6: Unmatched payments per merchant (GROUP BY)
        unmatched_payments_by_merchant = db.query(
            Payment.merchant_id,
            func.count(Payment.id).label('count')
        ).filter(
            Payment.status == PaymentStatus.completed,
            Payment.merchant_id.isnot(None)
        ).group_by(Payment.merchant_id).all()
        
        # Combine results into merchants_summary
        # Convert query results to dictionaries for easy lookup
        reconciled_dict = {row[0]: {'count': row[1], 'amount': float(row[2] or 0)} 
                           for row in reconciled_by_merchant}
        unmatched_orders_dict = {row[0]: row[1] 
                                 for row in unmatched_orders_by_merchant}
        unmatched_payments_dict = {row[0]: row[1] 
                                   for row in unmatched_payments_by_merchant}
        
        # Get all unique merchant IDs across all queries
        all_merchant_ids = (set(reconciled_dict.keys()) | 
                            set(unmatched_orders_dict.keys()) | 
                            set(unmatched_payments_dict.keys()))
        
        # Build summary for each merchant
        merchants_summary = []
        for merchant_id in all_merchant_ids:
            merchants_summary.append({
                "merchant_id": merchant_id,
                "reconciled_count": reconciled_dict.get(merchant_id, {}).get('count', 0),
                "reconciled_amount": reconciled_dict.get(merchant_id, {}).get('amount', 0.0),
                "unmatched_orders": unmatched_orders_dict.get(merchant_id, 0),
                "unmatched_payments": unmatched_payments_dict.get(merchant_id, 0)
            })
        
        logger.info(f"Report generated successfully: {len(merchants_summary)} merchants analyzed")

        return ReconciliationReport(
            total_reconciled_amount=reconciled_amount,
            total_reconciled_count=reconciled_count,
            total_unmatched_orders=unmatched_orders_count,
            total_unmatched_payments=unmatched_payments_count,
            unmatched_orders_amount=unmatched_orders_amount,
            unmatched_payments_amount=unmatched_payments_amount,
            merchants_summary=merchants_summary
        )
        
    except Exception as e:
        logger.error(f"Error generating reconciliation report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the report"
        )





@app.get("/discrepancies", response_model=DiscrepanciesResponse)
def get_discrepancies(db: Session = Depends(get_db)):
    """
    Get detailed list of unmatched transactions.
    
    Returns:
    - All completed orders without matching payments
    - All completed payments without matching orders
    
    Use this to investigate specific discrepancies found in the report.
    """
    logger.info("Generating discrepancies list")
    
    try:
        # Get unmatched ORDERS (completed but not reconciled)
        unmatched_orders = db.query(Order).filter(
            Order.status == OrderStatus.completed
        ).all()
        
        # Get unmatched PAYMENTS (completed but not reconciled)
        unmatched_payments = db.query(Payment).filter(
            Payment.status == PaymentStatus.completed
        ).all()
        
        logger.info(
            f"Found {len(unmatched_orders)} unmatched orders and "
            f"{len(unmatched_payments)} unmatched payments"
        )
        
        logger.info("Discrepancies list generated successfully")
        
        return DiscrepanciesResponse(
            unmatched_orders=unmatched_orders,
            unmatched_payments=unmatched_payments
        )
        
    except Exception as e:
        logger.error(f"Error generating discrepancies list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving discrepancies"
        )