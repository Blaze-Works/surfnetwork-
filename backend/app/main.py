# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core import mc
from app.routers import admin, cart, forums, login, register

app = FastAPI(title="SurfNetwork API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)
app.include_router(cart.router)
app.include_router(forums.router)
app.include_router(login.router)
app.include_router(register.router)
app.include_router(mc.router)

app.mount("/public", StaticFiles(directory="public"), name="public")

@app.get("/health-check")
def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Welcome to the SurfNetwork API"}
