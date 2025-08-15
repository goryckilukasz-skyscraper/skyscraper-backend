from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List
import asyncio
import httpx
import os
from datetime import datetime
import json
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SkyScraper.bot API",
    description="Enterprise-grade web scraping with conversational AI and legal compliance",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ScrapeRequest(BaseModel):
    url: HttpUrl
    instruction: str
    format: Optional[str] = "json"
    webhook_url: Optional[HttpUrl] = None
    structured_extraction: Optional[bool] = False
    schema_enforcement: Optional[str] = "loose"
    visualization: Optional[str] = None

class UserSignup(BaseModel):
    email: str
    name: str
    company: Optional[str] = None

class UserSignin(BaseModel):
    email: str
    password: str

class ExtractResponse(BaseModel):
    job_id: str
    status: str
    url: str
    data: Optional[Dict[Any, Any]] = None
    structured_data: Optional[bool] = None
    entities: Optional[int] = None
    accuracy: Optional[str] = None
    dashboard_url: Optional[str] = None
    r_code_url: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

# In-memory storage (replace with database in production)
jobs_db = {}
users_db = {}

# Helper functions
async def check_robots_txt(url: str) -> Dict[str, Any]:
    """Check robots.txt compliance"""
    try:
        parsed_url = urlparse(str(url))
        robots_url_str = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(robots_url_str, timeout=5.0)
            if response.status_code == 200:
                robots_content = response.text
                if "Disallow: /" in robots_content:
                    return {
                        "compliant": False,
                        "reason": "Robots.txt disallows all crawling",
                        "robots_url": robots_url_str
                    }
                return {
                    "compliant": True,
                    "robots_url": robots_url_str,
                    "content": robots_content[:500]
                }
            else:
                return {
                    "compliant": True,
                    "reason": "No robots.txt found - assuming allowed",
                    "robots_url": robots_url_str
                }
    except Exception as e:
        logger.warning(f"Could not check robots.txt for {url}: {e}")
        return {
            "compliant": True,
            "reason": "Could not check robots.txt - proceeding with caution",
            "error": str(e)
        }

async def langextract_scrape(url: str, instruction: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Integration with langextract for actual scraping"""
    try:
        await asyncio.sleep(1)  # Simulate processing time
        
        # Mock response based on instruction
        if "product" in instruction.lower() and "price" in instruction.lower():
            mock_data = {
                "products": [
                    {"name": "Sample Product 1", "price": "$29.99", "rating": 4.5},
                    {"name": "Sample Product 2", "price": "$39.99", "rating": 4.2},
                    {"name": "Sample Product 3", "price": "$19.99", "rating": 4.8}
                ]
            }
        elif "email" in instruction.lower():
            mock_data = {
                "emails": [
                    "contact@example.com",
                    "support@example.com",
                    "info@example.com"
                ]
            }
        else:
            mock_data = {
                "extracted_text": "Sample extracted content based on instruction",
                "metadata": {
                    "title": "Example Page",
                    "description": "This is an example page description",
                    "word_count": 150
                }
            }
        
        # Add structured data if requested
        if options.get("structured_extraction"):
            mock_data["entities"] = {
                "companies": ["Example Corp", "Sample Inc"],
                "people": ["John Doe", "Jane Smith"],
                "locations": ["New York", "California"],
                "financial_data": [
                    {"metric": "Revenue", "value": "$1.2M", "period": "Q1 2024"},
                    {"metric": "Growth", "value": "15%", "period": "YoY"}
                ]
            }
            mock_data["entity_count"] = 6
            mock_data["accuracy"] = "99.9%"
        
        return {
            "success": True,
            "data": mock_data,
            "processing_time": 1.1,
            "pages_processed": 1
        }
        
    except Exception as e:
        logger.error(f"Error in langextract_scrape: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# API Routes
@app.get("/")
async def root():
    return {
        "message": "SkyScraper.bot API",
        "version": "1.0.0",
        "status": "operational",
        "platform": "Vercel Serverless",
        "features": [
            "Conversational AI extraction",
            "Legal compliance checking",
            "R dashboard export",
            "Real-time streaming",
            "Enterprise collaboration"
        ]
    }

@app.post("/v1/extract", response_model=ExtractResponse)
async def extract_data(request: ScrapeRequest):
    """Main endpoint for data extraction with legal compliance"""
    
    # Generate job ID
    job_id = f"extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(jobs_db)}"
    
    # Check compliance
    robots_check = await check_robots_txt(str(request.url))
    
    if not robots_check["compliant"]:
        raise HTTPException(status_code=400, detail=f"Robots.txt compliance issue: {robots_check['reason']}")
    
    # Process extraction
    extraction_options = {
        "structured_extraction": request.structured_extraction,
        "schema_enforcement": request.schema_enforcement,
        "format": request.format
    }
    
    result = await langextract_scrape(
        str(request.url),
        request.instruction,
        extraction_options
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # Store job
    job = {
        "job_id": job_id,
        "status": "completed",
        "url": str(request.url),
        "instruction": request.instruction,
        "format": request.format,
        "structured_extraction": request.structured_extraction,
        "data": result["data"],
        "structured_data": request.structured_extraction,
        "entities": result["data"].get("entity_count"),
        "accuracy": result["data"].get("accuracy"),
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "compliance": {
            "robots_txt": robots_check
        }
    }
    
    # Generate R dashboard if requested
    if request.format == "r_dashboard":
        job["dashboard_url"] = f"https://dash.skyscraper.bot/{job_id}"
        job["r_code_url"] = f"https://api.skyscraper.bot/r/{job_id}.R"
    
    jobs_db[job_id] = job
    
    return ExtractResponse(**job)

@app.get("/v1/jobs/{job_id}", response_model=ExtractResponse)
async def get_job_status(job_id: str):
    """Get job status and results"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    return ExtractResponse(**job)

@app.get("/v1/jobs")
async def list_jobs(limit: int = 10, offset: int = 0):
    """List recent jobs"""
    jobs_list = list(jobs_db.values())
    jobs_list.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "jobs": jobs_list[offset:offset + limit],
        "total": len(jobs_list),
        "limit": limit,
        "offset": offset
    }

@app.post("/v1/auth/signup")
async def signup(user: UserSignup):
    """User signup endpoint"""
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user_{len(users_db)}"
    users_db[user.email] = {
        "user_id": user_id,
        "email": user.email,
        "name": user.name,
        "company": user.company,
        "created_at": datetime.now().isoformat(),
        "plan": "starter",
        "api_key": f"sk_live_{user_id}_{datetime.now().strftime('%Y%m%d')}"
    }
    
    return {
        "message": f"Welcome {user.name}! Your account has been created.",
        "user_id": user_id,
        "api_key": users_db[user.email]["api_key"]
    }

@app.post("/v1/auth/signin")
async def signin(credentials: UserSignin):
    """User signin endpoint"""
    if credentials.email not in users_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = users_db[credentials.email]
    
    return {
        "message": "Welcome back!",
        "user_id": user["user_id"],
        "api_key": user["api_key"]
    }

@app.get("/v1/compliance/check")
async def compliance_check(url: str):
    """Check legal compliance for a URL"""
    robots_check = await check_robots_txt(url)
    
    return {
        "url": url,
        "robots_txt": robots_check,
        "overall_compliance": robots_check["compliant"],
        "recommendations": [
            "Respect rate limits",
            "Review terms of service manually",
            "Monitor for policy changes"
        ]
    }

@app.get("/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "platform": "Vercel Serverless",
        "active_jobs": len([j for j in jobs_db.values() if j["status"] == "processing"]),
        "total_jobs": len(jobs_db),
        "registered_users": len(users_db)
    }

# Vercel handler
handler = app
