from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": "SkyScraper.bot API", 
        "status": "operational",
        "version": "1.0.0"
    }

@app.get("/v1/health")
def health():
    return {"status": "healthy", "platform": "Vercel"}

@app.get("/test")
def test():
    return {"test": "working!"}
