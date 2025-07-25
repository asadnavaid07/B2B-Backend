from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, ForeignKey,Text,JSON,Float
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime



class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    users = relationship("ProductCategory", back_populates="category")


class ProductCategory(Base):
    __tablename__ = "product_categories"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), primary_key=True)
    user = relationship("User")
    category = relationship("Category")