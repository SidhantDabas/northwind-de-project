from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, DateTime, func, Column, Integer, Boolean, Float, ForeignKey, String, text, distinct
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from database import get_db
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

router = APIRouter(prefix="/products", tags=["products"])

PAGE_SIZE = 20
# Setup Base for ORM
Base = declarative_base()
    
class ProductORM(Base):
    __tablename__ = "Products"
    ProductID = Column(Integer, primary_key=True, index=True)
    ProductName = Column(String)
    QuantityPerUnit = Column(String)
    UnitPrice = Column(Float)
    UnitsInStock = Column(Integer)
    Discontinued = Column(Boolean)
    CategoryID = Column(Integer, ForeignKey("Categories.CategoryID"))
    SupplierID = Column(Integer, ForeignKey("Suppliers.SupplierID"))
class ProductSchema(BaseModel):
    ProductID: int
    ProductName: str
    QuantityPerUnit: str
    UnitPrice: float
    UnitsInStock: int
    Discontinued: bool

    model_config = ConfigDict(from_attributes=True)
       
class SupplierORM(Base):
    __tablename__ = "Suppliers"
    SupplierID = Column(Integer, primary_key=True, index=True)
    CompanyName = Column(String)
class SupplierSchema(BaseModel):
    SupplierID: int
    CompanyName: str

    model_config = ConfigDict(from_attributes=True)
 
class CategoryORM(Base):
    __tablename__ = "Categories"
    CategoryID = Column(Integer, primary_key=True, index=True)
    CategoryName = Column(String)
class CategorySchema(BaseModel):
    CategoryID: int
    CategoryName: str

    model_config = ConfigDict(from_attributes=True)    

@router.get("/")
def get_products(
    page: int = Query(default=1, ge=1),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * PAGE_SIZE
    params = {"limit": PAGE_SIZE, "offset": offset}
    stmt = select(
    ProductORM.ProductID,
    ProductORM.ProductName,
    ProductORM.QuantityPerUnit,
    ProductORM.UnitPrice,
    ProductORM.UnitsInStock,
    ProductORM.Discontinued,
    CategoryORM.CategoryName,
    SupplierORM.CompanyName.label("SupplierName")
).join(CategoryORM, ProductORM.CategoryID == CategoryORM.CategoryID
).join(SupplierORM, ProductORM.SupplierID == SupplierORM.SupplierID)
    
    stmt = stmt.order_by(ProductORM.ProductName).limit(PAGE_SIZE).offset(offset)
    count_stmt = select(func.count(distinct(ProductORM.ProductID)))
    
    rows = db.execute(stmt).mappings().all()

    total = db.execute(count_stmt).scalar() or 0
    total_pages = -(-total // PAGE_SIZE)

    return {
        "data": [dict(r) for r in rows],
        "pagination": {
            "page": page,
            "page_size": PAGE_SIZE,
            "total_records": total,
            "total_pages": total_pages,
            "next_page": page + 1 if page < total_pages else None
        }
    }