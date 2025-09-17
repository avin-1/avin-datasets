# models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()

class Customer(Base):
    __tablename__ = 'Customers'
    customer_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    city = Column(String)
    signup_date = Column(Date)
    phone_number = Column(String, nullable=True)
    orders = relationship("Order", back_populates="customer")

class Employee(Base):
    __tablename__ = 'Employees'
    employee_id = Column(Integer, primary_key=True)
    name = Column(String)
    role = Column(String)
    hire_date = Column(Date)
    salary = Column(Float)
    department = relationship("Department", back_populates="manager")
    orders = relationship("Order", back_populates="employee")

class Department(Base):
    __tablename__ = 'Departments'
    department_id = Column(Integer, primary_key=True)
    name = Column(String)
    manager_id = Column(Integer, ForeignKey('Employees.employee_id'))
    manager = relationship("Employee", back_populates="department")
    products = relationship("Product", back_populates="department")

class Product(Base):
    __tablename__ = 'Products'
    product_id = Column(Integer, primary_key=True)
    name = Column(String)
    category = Column(String)
    price = Column(Float)
    department_id = Column(Integer, ForeignKey('Departments.department_id'))
    department = relationship("Department", back_populates="products")
    inventory = relationship("Inventory", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")

class Inventory(Base):
    __tablename__ = 'Inventory'
    inventory_id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('Products.product_id'))
    stock_level = Column(Integer)
    last_update = Column(DateTime)
    product = relationship("Product", back_populates="inventory")

class Order(Base):
    __tablename__ = 'Orders'
    order_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('Customers.customer_id'))
    employee_id = Column(Integer, ForeignKey('Employees.employee_id'))
    order_date = Column(DateTime)
    status = Column(String)
    customer = relationship("Customer", back_populates="orders")
    employee = relationship("Employee", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")
    payments = relationship("Payment", back_populates="order")

class OrderItem(Base):
    __tablename__ = 'OrderItems'
    order_item_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('Orders.order_id'))
    product_id = Column(Integer, ForeignKey('Products.product_id'))
    quantity = Column(Integer)
    unit_price = Column(Float)
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")

class Payment(Base):
    __tablename__ = 'Payments'
    payment_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('Orders.order_id'))
    amount = Column(Float)
    payment_date = Column(DateTime)
    method = Column(String)
    order = relationship("Order", back_populates="payments")