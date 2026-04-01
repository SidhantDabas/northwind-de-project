from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, DateTime, func, Column, Integer, Float, ForeignKey, String, text, distinct
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from database import get_db
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/orders", tags=["orders"])

PAGE_SIZE = 50
# Setup Base for ORM
Base = declarative_base()

# SQLAlchemy ORM Model and pydantic for Orders and Order Details
class OrdersORM(Base):
    __tablename__ = "Orders"
    OrderID = Column(Integer, primary_key=True, index=True)
    CustomerID = Column(String)
    EmployeeID = Column(Integer)
    OrderDate = Column(DateTime)
    ShippedDate = Column(DateTime)
    Freight = Column(Float)
    ShipCity = Column(String)
    ShipCountry = Column(String)

class OrdersSchema(BaseModel):
    OrderID: int
    CustomerID: str
    EmployeeID: int
    OrderDate: Optional[datetime]
    ShippedDate: Optional[datetime]
    Freight: Optional[float]
    ShipCity: Optional[str]
    ShipCountry: Optional[str]
    
    # Enable compatibility with SQLAlchemy Row/Mapping objects
    model_config = ConfigDict(from_attributes=True)
    
class Orders_detailsORM(Base):
    __tablename__ = "Order Details"
    OrderID = Column(Integer, primary_key=True, index=True)
    ProductID = Column(Integer, primary_key=True, index=True)
    UnitPrice = Column(Float)
    Quantity = Column(Integer)
    Discount = Column(Float)
    
    @hybrid_property
    def LineTotal(self):
        return self.UnitPrice * self.Quantity * (1 - self.Discount)

class Orders_detailsSchema(BaseModel):
    OrderID: int
    ProductID: int
    UnitPrice: float
    Quantity: int
    Discount: float

    # Enable compatibility with SQLAlchemy Row/Mapping objects
    model_config = ConfigDict(from_attributes=True)
    
@router.get("/")
def get_orders(
    page: int = Query(default=1, ge=1),
    customer_id: str = Query(default=None),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * PAGE_SIZE

    # Get paginated order IDs first
    id_stmt = select(OrdersORM.OrderID)
    count_stmt = select(func.count(distinct(OrdersORM.OrderID)))

    if customer_id:
        id_stmt = id_stmt.where(OrdersORM.CustomerID == customer_id)
        count_stmt = count_stmt.where(OrdersORM.CustomerID == customer_id)

    id_stmt = id_stmt.order_by(OrdersORM.OrderDate).limit(PAGE_SIZE).offset(offset)
    order_ids = [row[0] for row in db.execute(id_stmt).all()]

    total = db.execute(count_stmt).scalar() or 0
    total_pages = -(-total // PAGE_SIZE)

    if not order_ids:
        return {
            "data": [],
            "pagination": {
                "page": page,
                "page_size": PAGE_SIZE,
                "total_records": total,
                "total_pages": total_pages,
                "next_page": page + 1 if page < total_pages else None
            }
        }

    # Fetch orders + line items for those IDs
    stmt = select(
        OrdersORM.OrderID,
        OrdersORM.CustomerID,
        OrdersORM.EmployeeID,
        OrdersORM.OrderDate,
        OrdersORM.ShippedDate,
        OrdersORM.Freight,
        OrdersORM.ShipCity,
        OrdersORM.ShipCountry,
        Orders_detailsORM.ProductID,
        Orders_detailsORM.UnitPrice,
        Orders_detailsORM.Quantity,
        Orders_detailsORM.Discount,
        (Orders_detailsORM.UnitPrice *
         Orders_detailsORM.Quantity *
         (1 - Orders_detailsORM.Discount)).label("LineTotal")
    ).join(
        Orders_detailsORM, OrdersORM.OrderID == Orders_detailsORM.OrderID
    ).where(
        OrdersORM.OrderID.in_(order_ids)
    ).order_by(OrdersORM.OrderDate, OrdersORM.OrderID)

    rows = db.execute(stmt).mappings().all()

    # Group line items under their parent order
    orders_dict = {}
    for row in rows:
        oid = row["OrderID"]
        if oid not in orders_dict:
            orders_dict[oid] = {
                "OrderID": row["OrderID"],
                "CustomerID": row["CustomerID"],
                "EmployeeID": row["EmployeeID"],
                "OrderDate": str(row["OrderDate"]),
                "ShippedDate": str(row["ShippedDate"]) if row["ShippedDate"] else None,
                "Freight": row["Freight"],
                "ShipCity": row["ShipCity"],
                "ShipCountry": row["ShipCountry"],
                "line_items": []
            }
        orders_dict[oid]["line_items"].append({
            "ProductID": row["ProductID"],
            "UnitPrice": row["UnitPrice"],
            "Quantity": row["Quantity"],
            "Discount": row["Discount"],
            "LineTotal": round(row["LineTotal"], 2)
        })

    return {
        "data": list(orders_dict.values()),
        "pagination": {
            "page": page,
            "page_size": PAGE_SIZE,
            "total_records": total,
            "total_pages": total_pages,
            "next_page": page + 1 if page < total_pages else None
        }
    }