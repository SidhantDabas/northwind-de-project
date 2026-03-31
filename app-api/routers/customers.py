from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, Column, String
from sqlalchemy.orm import Session, declarative_base
from database import get_db
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# Setup Base for ORM
Base = declarative_base()

# SQLAlchemy ORM Model for Customers
class CustomerORM(Base):
    __tablename__ = "Customers"
    CustomerID = Column(String, primary_key=True, index=True)
    CompanyName = Column(String)
    ContactName = Column(String)
    ContactTitle = Column(String)
    City = Column(String)
    Country = Column(String)
    Phone = Column(String)

# Pydantic Schema for Response
class CustomerSchema(BaseModel):
    CustomerID: str
    CompanyName: str
    ContactName: str
    ContactTitle: str
    City: str
    Country: str
    Phone: str
    
    # Enable compatibility with SQLAlchemy Row/Mapping objects
    model_config = ConfigDict(from_attributes=True)

router = APIRouter(prefix="/customers", tags=["customers"])
PAGE_SIZE = 20

@router.get("/")
def get_customers(
    page: int = Query(default=1, ge=1),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * PAGE_SIZE
    
    # Define specific columns
    columns = [
        CustomerORM.CustomerID, CustomerORM.CompanyName, CustomerORM.ContactName,
        CustomerORM.ContactTitle, CustomerORM.City, CustomerORM.Country, CustomerORM.Phone
    ]
    
    # Execute Paginated Query (Modern 2.0 Style)
    stmt = select(*columns).limit(PAGE_SIZE).offset(offset)
    # .mappings() is excellent for converting to dicts
    rows = db.execute(stmt).mappings().all()

    # Optimized Count Query
    total = db.execute(select(func.count()).select_from(CustomerORM)).scalar()
    
    total_pages = -(-total // PAGE_SIZE) 

    return {
        "data": rows, # FastAPI + Pydantic handles the dict conversion automatically
        "pagination": {
            "page": page,
            "page_size": PAGE_SIZE,
            "total_records": total,
            "total_pages": total_pages,
            "next_page": page + 1 if page < total_pages else None
        }
    }