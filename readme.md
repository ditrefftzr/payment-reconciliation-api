# Payment Reconciliation API

A RESTful API built with FastAPI for managing payment reconciliation workflows. This project demonstrates backend development skills with Python, database design with MySQL, and understanding of financial reconciliation processes.

## 🎯 Project Overview

This API simulates a payment reconciliation system where:
- **Merchants** submit orders (expected transactions)
- **Payment processors** send payment records (actual transactions)
- The system **reconciles** payments against orders using matching algorithms
- **Discrepancies** are identified and reported for investigation

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.128.0
- **Database**: MySQL 8.0
- **ORM**: SQLAlchemy 2.0.46
- **Validation**: Pydantic 2.12.5
- **Server**: Uvicorn
- **Language**: Python 3.13

## 📊 Database Architecture

Three-table normalized design with foreign key relationships:

```
merchants
├── id (PK, auto-increment)
├── merchant_id (unique business identifier)
└── merchant_name

orders
├── id (PK)
├── merchant_id (FK → merchants.id)
├── merchant_order_id (unique)
├── amount, currency, description
├── order_date
└── status (pending/completed/failed/reconciled)

payments
├── id (PK)
├── merchant_id (FK → merchants.id)
├── merchant_order_id (unique)
├── amount, currency, description
├── payment_date
└── status (pending/completed/failed/reconciled)
```

## 🚀 Setup Instructions

### Prerequisites
- Python 3.9+
- MySQL 8.0+

### 1. Clone the Repository
```bash
git clone https://github.com/ditrefftzr/payment-reconciliation-api.git
cd payment-reconciliation-api
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Database
Create a `.env` file in the project root:
```env
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=payment_reconciliation
```

### 5. Initialize Database
The initialization script will create the database and tables automatically:
```bash
python scripts/init_db.py
```

### 6. Run the Server
```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`

Interactive API documentation: `http://localhost:8000/docs`

## 📚 API Endpoints

### Merchant Management
```http
POST   /merchants              # Create new merchant
GET    /merchants              # List all merchants
GET    /merchants/{merchant_id} # Get specific merchant
```

### Order Management
```http
POST   /orders                 # Create new order
GET    /orders                 # List all orders
GET    /orders/{merchant_order_id} # Get specific order
```

### Payment Management
```http
POST   /payments               # Create new payment
GET    /payments               # List all payments
GET    /payments/{merchant_order_id} # Get specific payment
```

### Reconciliation
```http
POST   /reconciliation         # Run reconciliation algorithm
GET    /reconciliation/report  # Get reconciliation summary
GET    /discrepancies          # Get unmatched transactions
```

## 💡 Example Usage

### 1. Create a Merchant
```bash
curl -X POST "http://localhost:8000/merchants" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "MERCHANT_A",
    "merchant_name": "Amazon"
  }'
```

### 2. Create an Order
```bash
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "MERCHANT_A",
    "merchant_order_id": "ORDER_001",
    "amount": 100.00,
    "currency": "USD",
    "order_date": "2025-01-29",
    "status": "completed"
  }'
```

### 3. Create a Payment
```bash
curl -X POST "http://localhost:8000/payments" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "MERCHANT_A",
    "merchant_order_id": "ORDER_001",
    "amount": 100.00,
    "currency": "USD",
    "payment_date": "2025-01-30",
    "status": "completed"
  }'
```

### 4. Run Reconciliation
```bash
curl -X POST "http://localhost:8000/reconciliation"
```

## 🔍 Reconciliation Algorithm

The system matches payments to orders using these rules:

1. **Same merchant_order_id** - Links payment to specific order
2. **Same merchant_id** - Both belong to same merchant
3. **Exact amount match** - Payment amount equals order amount
4. **Date tolerance** - Payment date within ±3 days of order date
5. **Status validation** - Both must have status='completed'

When matched, both transactions are marked as `reconciled`. Unmatched transactions are flagged for investigation.

## 🏗️ Project Structure

```
payment-reconciliation-api/
├── app/
│   ├── main.py              # API endpoints
│   ├── database.py          # Database connection
│   ├── logger.py            # Logging configuration
│   ├── models/
│   │   └── db_schema.py     # SQLAlchemy models
│   └── schemas/
│       ├── merchant.py      # Pydantic schemas
│       ├── order.py
│       ├── payment.py
│       └── reconciliation.py
├── scripts/
│   └── init_db.py           # Database initialization
├── .env                     # Environment variables (not in git)
├── .gitignore
├── requirements.txt
└── README.md
```

## 🎓 Key Features

### Backend Development
- RESTful API design with FastAPI
- CRUD operations with proper HTTP methods
- Request validation using Pydantic
- Auto-generated OpenAPI/Swagger documentation

### Database Engineering
- Normalized database design
- Foreign key relationships
- SQLAlchemy ORM patterns
- Efficient querying with aggregations

### Financial Domain
- Payment reconciliation workflows
- Transaction lifecycle management
- Discrepancy detection and reporting
- Decimal precision for monetary values

## 🧪 Testing

Test the API using:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **cURL** or **Postman**

## 📈 Future Enhancements

- Authentication & authorization
- Comprehensive test suite (pytest)
- Advanced reconciliation rules (partial payments)
- Export functionality (CSV reports)
- Docker containerization

## 👤 Author

**David Trefftz**
- Finance + Data Engineering background
- Portfolio project demonstrating backend API development

## 📄 License

MIT License - Available for educational purposes.
