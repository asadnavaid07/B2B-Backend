from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, ForeignKey,Text,JSON,Float
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)  # e.g., Boutique, Embroidery
    subcategory = Column(String(100), nullable=False)  # e.g., Pashmina, Sozni

class ProductCategory(Base):
    __tablename__ = "product_categories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)