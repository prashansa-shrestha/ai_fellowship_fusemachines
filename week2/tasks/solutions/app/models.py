# app/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Customer(Base):
    __tablename__ = "customers"  # must match exactly the table name in seed.sql

    customerNumber = Column(Integer, primary_key=True, index=True)
    customerName = Column(String(50), nullable=False)
    contactLastName = Column(String(50), nullable=False)
    contactFirstName = Column(String(50), nullable=False)
    phone = Column(String(50), nullable=False)
    addressLine1 = Column(String(50), nullable=False)
    addressLine2 = Column(String(50), nullable=True)
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=True)
    postalCode = Column(String(15), nullable=True)
    country = Column(String(50), nullable=False)
    salesRepEmployeeNumber = Column(Integer, ForeignKey("employees.employeeNumber"), nullable=True)
    creditLimit = Column(Float, nullable=True)

    # Relationships — SQLAlchemy will automatically JOIN these tables when needed
    orders = relationship("Order", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    orderNumber = Column(Integer, primary_key=True, index=True)
    orderDate = Column(Date, nullable=False)
    requiredDate = Column(Date, nullable=False)
    shippedDate = Column(Date, nullable=True)
    status = Column(String(15), nullable=False)
    comments = Column(Text, nullable=True)
    customerNumber = Column(Integer, ForeignKey("customers.customerNumber"), nullable=False)

    customer = relationship("Customer", back_populates="orders")


class Payment(Base):
    __tablename__ = "payments"

    customerNumber = Column(Integer, ForeignKey("customers.customerNumber"), primary_key=True)
    checkNumber = Column(String(50), primary_key=True)
    paymentDate = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)

    customer = relationship("Customer", back_populates="payments")

    # app/models.py  — ADD these classes below your existing ones

class Product(Base):
    __tablename__ = "products"

    productCode = Column(String(15), primary_key=True, index=True)
    productName = Column(String(70), nullable=False)
    productLine = Column(String(50), ForeignKey("productlines.productLine"), nullable=False)
    productScale = Column(String(10), nullable=False)
    productVendor = Column(String(50), nullable=False)
    productDescription = Column(Text, nullable=False)
    quantityInStock = Column(Integer, nullable=False)
    buyPrice = Column(Float, nullable=False)
    MSRP = Column(Float, nullable=False)


class ProductLine(Base):
    __tablename__ = "productlines"

    productLine = Column(String(50), primary_key=True, index=True)
    textDescription = Column(String(4000), nullable=True)
    htmlDescription = Column(Text, nullable=True)
    image = Column(Text, nullable=True)  # stored as bytea/text in some seeds


class Employee(Base):
    __tablename__ = "employees"

    employeeNumber = Column(Integer, primary_key=True, index=True)
    lastName = Column(String(50), nullable=False)
    firstName = Column(String(50), nullable=False)
    extension = Column(String(10), nullable=False)
    email = Column(String(100), nullable=False)
    officeCode = Column(String(10), ForeignKey("offices.officeCode"), nullable=False)
    reportsTo = Column(Integer, ForeignKey("employees.employeeNumber"), nullable=True)
    jobTitle = Column(String(50), nullable=False)


class Office(Base):
    __tablename__ = "offices"

    officeCode = Column(String(10), primary_key=True, index=True)
    city = Column(String(50), nullable=False)
    phone = Column(String(50), nullable=False)
    addressLine1 = Column(String(50), nullable=False)
    addressLine2 = Column(String(50), nullable=True)
    state = Column(String(50), nullable=True)
    country = Column(String(50), nullable=False)
    postalCode = Column(String(15), nullable=False)
    territory = Column(String(10), nullable=False)


class OrderDetail(Base):
    __tablename__ = "orderdetails"

    orderNumber = Column(Integer, ForeignKey("orders.orderNumber"), primary_key=True)
    productCode = Column(String(15), ForeignKey("products.productCode"), primary_key=True)
    quantityOrdered = Column(Integer, nullable=False)
    priceEach = Column(Float, nullable=False)
    orderLineNumber = Column(Integer, nullable=False)