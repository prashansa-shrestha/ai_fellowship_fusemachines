# app/crud.py
from sqlalchemy.orm import Session
from app import models, schemas
from app.logger import get_logger

logger = get_logger(__name__)


# ── READ: Get all customers (with pagination) ──────────────────
def get_customers(db: Session, skip: int = 0, limit: int = 10):
    """
    skip: how many records to skip (for pagination)
    limit: max number of records to return
    
    Example: skip=20, limit=10 → page 3 (records 21-30)
    """
    logger.info(f"Fetching customers: skip={skip}, limit={limit}")
    customers = db.query(models.Customer).offset(skip).limit(limit).all()
    logger.info(f"Fetched {len(customers)} customers")
    return customers


# ── READ: Get single customer by ID ───────────────────────────
def get_customer(db: Session, customer_number: int):
    logger.info(f"Fetching customer with ID: {customer_number}")
    customer = (
        db.query(models.Customer)
        .filter(models.Customer.customerNumber == customer_number)
        .first()   # .first() returns None if not found (not an error)
    )
    if customer is None:
        logger.warning(f"Customer not found: ID {customer_number}")
    else:
        logger.info(f"Customer found: {customer.customerName}")
    return customer


# ── CREATE: Add new customer ───────────────────────────────────
def create_customer(db: Session, customer: schemas.CustomerCreate):
    logger.info(f"Creating new customer: {customer.customerName}")
    
    # Convert Pydantic schema → SQLAlchemy model
    # model_dump() turns the Pydantic object into a plain dictionary
    db_customer = models.Customer(**customer.model_dump())
    
    db.add(db_customer)    # stage the new record
    db.commit()            # actually write to database
    db.refresh(db_customer)  # reload from DB (gets the auto-generated ID)
    
    logger.info(f"Customer created successfully: ID {db_customer.customerNumber}")
    return db_customer


# ── UPDATE: Modify existing customer ──────────────────────────
def update_customer(db: Session, customer_number: int, updates: schemas.CustomerUpdate):
    logger.info(f"Updating customer ID: {customer_number}")
    
    db_customer = get_customer(db, customer_number)
    if db_customer is None:
        return None

    # Only update fields that were actually provided (not None)
    update_data = updates.model_dump(exclude_unset=True)  # exclude_unset is KEY here
    for field, value in update_data.items():
        setattr(db_customer, field, value)  # dynamically set attribute

    db.commit()
    db.refresh(db_customer)
    logger.info(f"Customer ID {customer_number} updated successfully")
    return db_customer


# ── DELETE: Remove customer ────────────────────────────────────
def delete_customer(db: Session, customer_number: int):
    logger.info(f"Deleting customer ID: {customer_number}")
    
    db_customer = get_customer(db, customer_number)
    if db_customer is None:
        return None

    db.delete(db_customer)
    db.commit()
    logger.info(f"Customer ID {customer_number} deleted successfully")
    return db_customer

# app/crud.py — ADD these functions below your existing CRUD functions

from app.database import SessionLocal   # import the session factory directly

# ── HELPER: creates its own session (needed for concurrency) ───
def _get_own_session():
    """
    Returns a new database session.
    Used by count functions called concurrently — each needs
    its own session to avoid thread-safety issues.
    """
    return SessionLocal()


# ── COUNT FUNCTIONS ────────────────────────────────────────────
# Each function:
#   1. Opens its own DB session
#   2. Runs a COUNT query
#   3. Closes the session (in finally block — always runs)
#   4. Returns an integer

def count_customers() -> int:
    db = _get_own_session()
    try:
        logger.info("Querying count: customers")
        result = db.query(models.Customer).count()
        logger.info(f"customers count = {result}")
        return result
    except Exception as e:
        logger.error(f"Error counting customers: {e}")
        return 0   # graceful fallback — return 0 instead of crashing
    finally:
        db.close()


def count_orders() -> int:
    db = _get_own_session()
    try:
        logger.info("Querying count: orders")
        result = db.query(models.Order).count()
        logger.info(f"orders count = {result}")
        return result
    except Exception as e:
        logger.error(f"Error counting orders: {e}")
        return 0
    finally:
        db.close()


def count_products() -> int:
    db = _get_own_session()
    try:
        logger.info("Querying count: products")
        result = db.query(models.Product).count()
        logger.info(f"products count = {result}")
        return result
    except Exception as e:
        logger.error(f"Error counting products: {e}")
        return 0
    finally:
        db.close()


def count_employees() -> int:
    db = _get_own_session()
    try:
        logger.info("Querying count: employees")
        result = db.query(models.Employee).count()
        logger.info(f"employees count = {result}")
        return result
    except Exception as e:
        logger.error(f"Error counting employees: {e}")
        return 0
    finally:
        db.close()


def count_offices() -> int:
    db = _get_own_session()
    try:
        logger.info("Querying count: offices")
        result = db.query(models.Office).count()
        logger.info(f"offices count = {result}")
        return result
    except Exception as e:
        logger.error(f"Error counting offices: {e}")
        return 0
    finally:
        db.close()


def count_payments() -> int:
    db = _get_own_session()
    try:
        logger.info("Querying count: payments")
        result = db.query(models.Payment).count()
        logger.info(f"payments count = {result}")
        return result
    except Exception as e:
        logger.error(f"Error counting payments: {e}")
        return 0
    finally:
        db.close()


def count_orderdetails() -> int:
    db = _get_own_session()
    try:
        logger.info("Querying count: orderdetails")
        result = db.query(models.OrderDetail).count()
        logger.info(f"orderdetails count = {result}")
        return result
    except Exception as e:
        logger.error(f"Error counting orderdetails: {e}")
        return 0
    finally:
        db.close()


def count_productlines() -> int:
    db = _get_own_session()
    try:
        logger.info("Querying count: productlines")
        result = db.query(models.ProductLine).count()
        logger.info(f"productlines count = {result}")
        return result
    except Exception as e:
        logger.error(f"Error counting productlines: {e}")
        return 0
    finally:
        db.close()