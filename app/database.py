# app/database.py
"""
Database connection and session management for MySQL.
This file creates the engine (connection to MySQL) and SessionLocal (factory for database sessions).
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load environment variables from .env file
load_dotenv()

# Build connection string from environment variables
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create the database engine - this is the actual connection to MySQL
# echo=True means SQLAlchemy will print all SQL queries (helpful for learning/debugging)
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# SessionLocal is a factory - each time we call SessionLocal(), we get a new database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all our SQLAlchemy models
Base = declarative_base()


# Dependency function for FastAPI
def get_db():
    """
    FastAPI dependency that provides a database session to each request.
    Automatically closes the session when the request is complete.
    """
    db = SessionLocal()  # Create a new session
    try:
        yield db  # Give it to the endpoint function
    finally:
        db.close()  # Always close the session (even if there's an error)