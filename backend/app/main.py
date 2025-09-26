# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.routers import admin, login, register

app = FastAPI(title="SurfNetwork API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)
app.include_router(login.router)
app.include_router(register.router)

app.mount("/public", StaticFiles(directory="public"), name="public")

@app.get('/get-server-ip')
async def reveal_ip():
    return {"ip": "No ip available"}

@app.get("/player-count")
async def player_count():
    return {"count": 0, "maxCount": 0}

@app.get("/get-server-stats")
async def server_stats():
    return {"ip": "No ip available", "online": False, "count": 0, "max": 0, "tps": 0, "version": "N/A", "uptime": "N/A", "total": 0, "average": 0, "motd": "N/A", "software": "N/A"}

@app.get("/health-check")
def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Welcome to the SurfNetwork API"}
