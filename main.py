from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List
import asyncio
import httpx
import uvicorn
import os
from datetime import datetime
import json
import logging
from urllib.parse import urlparse, robots_url
import re

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
                # Simple robots.txt parsing (implement more sophisticated parsing)
                if "Disallow: /" in robots_content:
                    return {
                        "compliant": False,
                        "reason": "Robots.txt disallows all crawling",
                        "robots_url": robots_url_str
                    }
                return {
                    "compliant": True,
                    "robots_url": robots_url_str,
                    "content": robots_content[:500]  # First 500 chars
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

async def analyze_terms_of_service(url: str) -> Dict[str, Any]:
    """AI-powered Terms of Service analysis"""
    # This would integrate with an AI service to analyze ToS
    # For now, return a mock analysis
    return {
        "scraping_allowed": True,
        "conditions": ["Respectful rate limiting", "No commercial use without permission"],
        "confidence": 0.85,
        "analysis": "Terms of service appear to allow automated access with rate limiting"
    }

async def langextract_scrape(url: str, instruction: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Integration with langextract for actual scraping"""
    try:
        # Mock langextract integration - replace with actual API calls
        # This would integrate with your langextract service
        
        await asyncio.sleep(2)  # Simulate processing time
        
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
            "processing_time": 2.1,
            "pages_processed": 1
        }
        
    except Exception as e:
        logger.error(f"Error in langextract_scrape: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def generate_r_dashboard(data: Dict[str, Any], job_id: str) -> Dict[str, str]:
    """Generate R dashboard and visualization code"""
    # Mock R dashboard generation
    r_code = """
# SkyScraper.bot Generated R Dashboard
library(shiny)
library(ggplot2)
library(dplyr)

# Load extracted data
data <- jsonlite::fromJSON('extracted_data.json')

# UI
ui <- fluidPage(
    titlePanel("SkyScraper.bot Data Dashboard"),
    sidebarLayout(
        sidebarPanel(
            selectInput("variable", "Choose Variable:", 
                       choices = names(data)),
            downloadButton("downloadData", "Download Data")
        ),
        mainPanel(
            plotOutput("dataPlot"),
            tableOutput("dataTable")
        )
    )
)

# Server
server <- function(input, output) {
    output$dataPlot <- renderPlot({
        # Generate appropriate plot based on data type
        ggplot(data) + theme_minimal()
    })
    
    output$dataTable <- renderTable({
        head(data, 20)
    })
}

shinyApp(ui = ui, server = server)
"""
    
    return {
        "dashboard_url": f"https://dash.skyscraper.bot/{job_id}",
        "r_code_url": f"https://api.skyscraper.bot/r/{job_id}.R",
        "r_code": r_code
    }

# API Routes
@app.get("/")
async def root():
    return {
        "message": "SkyScraper.bot API",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "Conversational AI extraction",
            "Legal compliance checking",
            "R dashboard export",
            "Real-time streaming",
            "Enterprise collaboration"
        ]
    }

@app.post("/v1/extract", response_model=ExtractResponse)
async def extract_data(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Main endpoint for data extraction with legal compliance"""
    
    # Generate job ID
    job_id = f"extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(jobs_db)}"
    
    # Initial job record
    job = {
        "job_id": job_id,
        "status": "processing",
        "url": str(request.url),
        "instruction": request.instruction,
        "format": request.format,
        "structured_extraction": request.structured_extraction,
        "created_at": datetime.now().isoformat(),
        "completed_at": None
    }
    
    jobs_db[job_id] = job
    
    # Start background processing
    background_tasks.add_task(
        process_extraction,
        job_id,
        request
    )
    
    return ExtractResponse(
        job_id=job_id,
        status="processing",
        url=str(request.url),
        created_at=job["created_at"]
    )

async def process_extraction(job_id: str, request: ScrapeRequest):
    """Background task to process extraction"""
    try:
        # Step 1: Legal compliance check
        robots_check = await check_robots_txt(str(request.url))
        tos_analysis = await analyze_terms_of_service(str(request.url))
        
        if not robots_check["compliant"]:
            jobs_db[job_id]["status"] = "failed"
            jobs_db[job_id]["error"] = f"Robots.txt compliance issue: {robots_check['reason']}"
            return
        
        # Step 2: Actual extraction
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
            jobs_db[job_id]["status"] = "failed"
            jobs_db[job_id]["error"] = result["error"]
            return
        
        # Step 3: Generate R dashboard if requested
        dashboard_info = {}
        if request.format == "r_dashboard":
            dashboard_info = await generate_r_dashboard(result["data"], job_id)
        
        # Step 4: Update job with results
        jobs_db[job_id].update({
            "status": "completed",
            "data": result["data"],
            "structured_data": request.structured_extraction,
            "entities": result["data"].get("entity_count"),
            "accuracy": result["data"].get("accuracy"),
            "completed_at": datetime.now().isoformat(),
            "compliance": {
                "robots_txt": robots_check,
                "terms_of_service": tos_analysis
            },
            **dashboard_info
        })
        
        # Step 5: Send webhook if provided
        if request.webhook_url:
            await send_webhook(str(request.webhook_url), jobs_db[job_id])
            
    except Exception as e:
        logger.error(f"Error processing extraction {job_id}: {e}")
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["error"] = str(e)

async def send_webhook(webhook_url: str, job_data: Dict[str, Any]):
    """Send webhook notification"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json=job_data, timeout=10.0)
    except Exception as e:
        logger.error(f"Failed to send webhook to {webhook_url}: {e}")

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
    
    # In production, hash password and store securely
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
    
    # In production, verify password hash
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
    tos_analysis = await analyze_terms_of_service(url)
    
    return {
        "url": url,
        "robots_txt": robots_check,
        "terms_of_service": tos_analysis,
        "overall_compliance": robots_check["compliant"] and tos_analysis["scraping_allowed"],
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
        "active_jobs": len([j for j in jobs_db.values() if j["status"] == "processing"]),
        "total_jobs": len(jobs_db),
        "registered_users": len(users_db)
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
