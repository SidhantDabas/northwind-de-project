from fastapi import FastAPI
from routers import customers, orders, products

app = FastAPI(title="Northwind CRM/ERP API", version="1.0.0")

app.include_router(customers.router)
app.include_router(orders.router)
app.include_router(products.router)

@app.get("/health")
def health():
    return {"status": "ok"}
