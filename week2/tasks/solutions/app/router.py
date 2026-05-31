
# app/router.py
import asyncio
import time
from functools import partial 
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app import schemas
from app.database import get_db
from app.logger import get_logger
from app import crud,models


logger = get_logger(__name__)

# APIRouter: like a mini-app for grouping related endpoints
# prefix: all URLs start with /customers
# tags: groups endpoints in the /docs page
router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/", response_model=List[schemas.CustomerListOut])
def list_customers(
    skip: int = Query(default=0, ge=0, description="Records to skip"),
    limit: int = Query(default=10, ge=1, le=100, description="Max records to return"),
    db: Session = Depends(get_db)   # ← Dependency Injection
):
    """
    List all customers with pagination.
    
    - **skip**: offset (default 0)
    - **limit**: page size (default 10, max 100)
    """
    logger.info(f"GET /customers called with skip={skip}, limit={limit}")
    customers = crud.get_customers(db, skip=skip, limit=limit)
    return customers


@router.get("/{customer_number}", response_model=schemas.CustomerOut)
def get_customer(customer_number: int, db: Session = Depends(get_db)):
    """
    Get a single customer by their customer number.
    Returns 404 if not found.
    """
    logger.info(f"GET /customers/{customer_number} called")
    customer = crud.get_customer(db, customer_number)
    
    if customer is None:
        logger.warning(f"404 returned for customer ID {customer_number}")
        raise HTTPException(status_code=404, detail=f"Customer {customer_number} not found")
    
    return customer


@router.post("/", response_model=schemas.CustomerOut, status_code=201)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    """
    Create a new customer.
    Returns 201 Created on success.
    """
    logger.info(f"POST /customers called for: {customer.customerName}")
    new_customer = crud.create_customer(db, customer)
    return new_customer


@router.patch("/{customer_number}", response_model=schemas.CustomerOut)
def update_customer(
    customer_number: int,
    updates: schemas.CustomerUpdate,
    db: Session = Depends(get_db)
):
    """
    Partially update a customer.
    Only provided fields are updated.
    """
    logger.info(f"PATCH /customers/{customer_number} called")
    updated = crud.update_customer(db, customer_number, updates)
    
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_number} not found")
    
    return updated


@router.delete("/{customer_number}", status_code=204)
def delete_customer(customer_number: int, db: Session = Depends(get_db)):
    """
    Delete a customer by number.
    Returns 204 No Content on success.
    """
    logger.info(f"DELETE /customers/{customer_number} called")
    deleted = crud.delete_customer(db, customer_number)
    
    if deleted is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_number} not found")
    
    # 204 means "success but no body to return"


counts_router = APIRouter(tags=["Table Counts"])


@counts_router.get("/customers/count", response_model=schemas.TableCount)
def get_customer_count(db: Session = Depends(get_db)):
    logger.info("GET /customers/count called")
    count = db.query(models.Customer).count()
    logger.info(f"customers/count response: {count}")
    return {"table": "customers", "count": count}


@counts_router.get("/orders/count", response_model=schemas.TableCount)
def get_order_count(db: Session = Depends(get_db)):
    logger.info("GET /orders/count called")
    count = db.query(models.Order).count()
    logger.info(f"orders/count response: {count}")
    return {"table": "orders", "count": count}


@counts_router.get("/products/count", response_model=schemas.TableCount)
def get_product_count(db: Session = Depends(get_db)):
    logger.info("GET /products/count called")
    count = db.query(models.Product).count()
    logger.info(f"products/count response: {count}")
    return {"table": "products", "count": count}


@counts_router.get("/employees/count", response_model=schemas.TableCount)
def get_employee_count(db: Session = Depends(get_db)):
    logger.info("GET /employees/count called")
    count = db.query(models.Employee).count()
    logger.info(f"employees/count response: {count}")
    return {"table": "employees", "count": count}


@counts_router.get("/offices/count", response_model=schemas.TableCount)
def get_office_count(db: Session = Depends(get_db)):
    logger.info("GET /offices/count called")
    count = db.query(models.Office).count()
    logger.info(f"offices/count response: {count}")
    return {"table": "offices", "count": count}


@counts_router.get("/payments/count", response_model=schemas.TableCount)
def get_payment_count(db: Session = Depends(get_db)):
    logger.info("GET /payments/count called")
    count = db.query(models.Payment).count()
    logger.info(f"payments/count response: {count}")
    return {"table": "payments", "count": count}


@counts_router.get("/orderdetails/count", response_model=schemas.TableCount)
def get_orderdetail_count(db: Session = Depends(get_db)):
    logger.info("GET /orderdetails/count called")
    count = db.query(models.OrderDetail).count()
    logger.info(f"orderdetails/count response: {count}")
    return {"table": "orderdetails", "count": count}


@counts_router.get("/productlines/count", response_model=schemas.TableCount)
def get_productline_count(db: Session = Depends(get_db)):
    logger.info("GET /productlines/count called")
    count = db.query(models.ProductLine).count()
    logger.info(f"productlines/count response: {count}")
    return {"table": "productlines", "count": count}


# ═══════════════════════════════════════════════════════════════
# PART 2: Aggregated Dashboard Endpoint — THE CONCURRENCY PART
# ═══════════════════════════════════════════════════════════════

dashboard_router = APIRouter(tags=["Dashboard"])


@dashboard_router.get("/overall_counts", response_model=schemas.OverallCounts)
async def get_overall_counts():
    """
    Fetches row counts from all 8 tables CONCURRENTLY.
    
    Key design decisions:
    - 'async def': marks this as an async endpoint
    - 'run_in_executor': runs blocking SQLAlchemy calls in a thread pool
      without blocking the event loop
    - 'asyncio.gather': launches all 8 tasks at the same time
    """
    logger.info("GET /overall_counts called — starting concurrent queries")
    start_time = time.time()   # track total execution time

    # Get the current event loop
    # The event loop is the engine that manages async tasks
    loop = asyncio.get_event_loop()

    # run_in_executor(None, func) explanation:
    #   - First arg None = use the default ThreadPoolExecutor
    #   - Second arg = the blocking function to run in a thread
    #   - Returns a coroutine (awaitable) that resolves when the thread finishes
    #
    # Why needed? SQLAlchemy queries are BLOCKING (synchronous).
    # If you call them directly in an async function, they freeze
    # the entire event loop. run_in_executor moves them to a
    # separate thread so other async work can continue.

    logger.info("Launching all 8 count queries concurrently via asyncio.gather")

    (
        customers,
        orders,
        products,
        employees,
        offices,
        payments,
        orderdetails,
        productlines,
    ) = await asyncio.gather(
        loop.run_in_executor(None, crud.count_customers),
        loop.run_in_executor(None, crud.count_orders),
        loop.run_in_executor(None, crud.count_products),
        loop.run_in_executor(None, crud.count_employees),
        loop.run_in_executor(None, crud.count_offices),
        loop.run_in_executor(None, crud.count_payments),
        loop.run_in_executor(None, crud.count_orderdetails),
        loop.run_in_executor(None, crud.count_productlines),
    )
    # asyncio.gather returns results IN ORDER — first arg's result is first,
    # second arg's result is second, etc. So the unpacking above is safe.

    elapsed = round(time.time() - start_time, 4)
    logger.info(f"asyncio.gather completed — all 8 queries finished in {elapsed}s")

    response = {
        "customers": customers,
        "orders": orders,
        "products": products,
        "employees": employees,
        "offices": offices,
        "payments": payments,
        "orderdetails": orderdetails,
        "productlines": productlines,
    }

    logger.info(f"GET /overall_counts response: {response}")
    return response