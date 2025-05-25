from sqlalchemy import create_engine, Column, String, Float, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    
    upc = Column(String, primary_key=True)
    fdc_id = Column(String, nullable=True)
    name = Column(String, nullable=False)
    ingredients = Column(String)
    nutrients = Column(JSON)
    branded_food_category = Column(String)
    dietary_tags = Column(JSON)
    price = Column(Float, nullable=True)
    store = Column(String, nullable=True)
    last_updated = Column(DateTime, nullable=True)

# Create SQLite database
engine = create_engine('sqlite:///grocery.db')
Base.metadata.create_all(engine)

# Create session factory
Session = sessionmaker(bind=engine)
session = Session()

def add_product(upc, name, ingredients, nutrients, categories, dietary, price=None, store=None, last_updated=None):
    """Add or update a product in the database."""
    product = session.query(Product).filter_by(upc=upc).first()
    if product:
        # Update existing product
        product.name = name
        product.ingredients = ingredients
        product.nutrients = nutrients
        product.branded_food_category = categories[0] if categories else None
        product.dietary_tags = dietary
        if price is not None:
            product.price = price
        if store is not None:
            product.store = store
        if last_updated is not None:
            product.last_updated = last_updated
    else:
        # Create new product
        product = Product(
            upc=upc,
            name=name,
            ingredients=ingredients,
            nutrients=nutrients,
            branded_food_category=categories[0] if categories else None,
            dietary_tags=dietary,
            price=price,
            store=store,
            last_updated=last_updated
        )
        session.add(product)
    session.commit() 