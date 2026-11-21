from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, properties, units, leases, payments, maintenance, dashboard

app = FastAPI(title="Property Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Property Management API is running"}


app.include_router(auth.router)
app.include_router(properties.router)
app.include_router(units.router)
app.include_router(leases.router)
app.include_router(payments.router)
app.include_router(maintenance.router)
app.include_router(dashboard.router)
