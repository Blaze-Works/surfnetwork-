# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.routers import admin, login, register
import os

app = FastAPI(title="SurfNetwork API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("DEV_IP"), "https://surfnetwork.xyz"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)
app.include_router(login.router)
app.include_router(register.router)

app.mount("/public", StaticFiles(directory="public"), name="public")

@app.get("/")
async def root():
    return {"message": "Welcome to the SurfNetwork API"}
