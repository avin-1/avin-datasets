# models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()

class Products(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Float)
    description = Column(String)
    # Add other columns as needed

class Orders(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    customer_name = Column(String)
    order_date = Column(String)
    # Add other columns as needed

# You can add more tables (e.g., OrderItems) as needed.