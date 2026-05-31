# app/schemas.py
from pydantic import BaseModel, field_validator, EmailStr
from typing import Optional, List
from datetime import date
import logging

logger = logging.getLogger(__name__)


# ── ORDER schemas ──────────────────────────────────────────────
class OrderBase(BaseModel):
    orderNumber: int
    orderDate: date
    requiredDate: date
    shippedDate: Optional[date] = None
    status: str
    comments: Optional[str] = None

    class Config:
        from_attributes = True   # allows Pydantic to read SQLAlchemy model objects


# ── PAYMENT schemas ────────────────────────────────────────────
class PaymentBase(BaseModel):
    checkNumber: str
    paymentDate: date
    amount: float

    class Config:
        from_attributes = True


# ── CUSTOMER schemas ───────────────────────────────────────────

class CustomerCreate(BaseModel):
    """Used when CREATING a new customer. No customerNumber (DB assigns it)."""
    customerName: str
    contactLastName: str
    contactFirstName: str
    phone: str
    addressLine1: str
    addressLine2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postalCode: Optional[str] = None
    country: str
    salesRepEmployeeNumber: Optional[int] = None
    creditLimit: Optional[float] = None

    @field_validator('customerName')
    @classmethod
    def name_must_not_be_empty(cls, v):
        """Custom validation: reject empty strings"""
        if not v.strip():
            logger.warning("Validation failed: customerName is empty")
            raise ValueError("customerName cannot be empty")
        return v

    @field_validator('creditLimit')
    @classmethod
    def credit_limit_must_be_positive(cls, v):
        if v is not None and v < 0:
            logger.warning(f"Validation failed: negative creditLimit {v}")
            raise ValueError("creditLimit cannot be negative")
        return v


class CustomerUpdate(BaseModel):
    """Used when UPDATING. All fields are optional (patch only what changed)."""
    customerName: Optional[str] = None
    contactLastName: Optional[str] = None
    contactFirstName: Optional[str] = None
    phone: Optional[str] = None
    addressLine1: Optional[str] = None
    addressLine2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postalCode: Optional[str] = None
    country: Optional[str] = None
    salesRepEmployeeNumber: Optional[int] = None
    creditLimit: Optional[float] = None


class CustomerOut(BaseModel):
    """What the USER SEES in the response. Includes related data."""
    customerNumber: int
    customerName: str
    contactLastName: str
    contactFirstName: str
    phone: str
    addressLine1: str
    addressLine2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postalCode: Optional[str] = None
    country: str
    salesRepEmployeeNumber: Optional[int] = None
    creditLimit: Optional[float] = None
    orders: List[OrderBase] = []       # default empty list if no orders
    payments: List[PaymentBase] = []   # default empty list if no payments

    class Config:
        from_attributes = True


class CustomerListOut(BaseModel):
    """Lightweight version for listing many customers (no orders/payments)."""
    customerNumber: int
    customerName: str
    city: str
    country: str
    creditLimit: Optional[float] = None

    class Config:
        from_attributes = True
    

class TableCount(BaseModel):
    """Response for a single table count endpoint."""
    table: str
    count: int


class OverallCounts(BaseModel):
    """Response for the /overall_counts dashboard endpoint."""
    customers: int
    orders: int
    products: int
    employees: int
    offices: int
    payments: int
    orderdetails: int
    productlines: int