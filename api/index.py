from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Create FastAPI app
app = FastAPI(title="SkyScraper.bot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple models
class UserSignup(BaseModel):
    email: str
    name: str
    company: Optional[str] = None

# In-memory storage
users_db = {}

# Routes
@app.get("/")
async def root():
    return {
        "message": "SkyScraper.bot API",
        "version": "1.0.0",
        "status": "operational",
        "platform": "Vercel Serverless",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/v1/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "platform": "Vercel",
        "users": len(users_db)
    }

@app.post("/v1/auth/signup")
async def signup(user: UserSignup):
    if user.email in users_db:
        return {"error": "Email already registered"}
    
    user_id = f"user_{len(users_db)}"
    users_db[user.email] = {
        "user_id": user_id,
        "email": user.email,
        "name": user.name,
        "company": user.company,
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "message": f"Welcome {user.name}!",
        "user_id": user_id
    }

@app.get("/v1/test")
async def test():
    return {"message": "API is working!", "test": True}
