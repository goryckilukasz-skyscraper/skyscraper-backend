import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import aiohttp
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, HttpUrl
import google.generativeai as genai
from playwright.async_api import async_playwright
import pandas as pd
import xml.etree.ElementTree as ET
from google.oauth2 import id_token
from google.auth.transport import requests
import io

# Configuration
GOOGLE_CLIENT_ID = "416380249965-ljohffe5opnfb3v52ehkq03svdogk99i.apps.googleusercontent.com"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCbVtyxS4f6ZWU8ceHm6wHEvEfi-2DA5Ag")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Initialize FastAPI
app = FastAPI(title="SkyScraper.bot API", version="1.0.0")

# CORS middleware - Allow your domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://skyscraper.bot",
        "https://www.skyscraper.bot", 
        "http://localhost:3000",
        "http://localhost:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models
class ScrapingRequest(BaseModel):
    url: HttpUrl
    instruction: str
    format: str = "json"
    anti_detection: bool = True
    extract_metadata: bool = True
    language: Optional[str] = "auto"

class UserAuth(BaseModel):
    token: str
    email: str
    name: str

class ScrapingResponse(BaseModel):
    job_id: str
    status: str
    data: Optional[Dict] = None
    metadata: Optional[Dict] = None
    download_urls: Optional[Dict] = None
    processing_time: Optional[float] = None

# In-memory storage (use Redis/database in production)
jobs_storage = {}
users_storage = {}

# Authentication
async def verify_google_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        # Verify Google OAuth token
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        return idinfo
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

# LangExtract Integration Class
class LangExtractProcessor:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def extract_metadata(self, content: str, url: str) -> Dict[str, Any]:
        """Extract structured metadata using Gemini/LangExtract approach"""
        prompt = f"""
        Analyze this web content and extract structured metadata. Return as JSON:
        
        Content from {url}:
        {content[:3000]}...
        
        Extract:
        1. document_type (article, product_page, blog, documentation, etc.)
        2. primary_topic (main subject/category)
        3. entities (people, companies, products mentioned)
        4. data_types (tables, lists, forms, images, etc.)
        5. language (detected language)
        6. content_structure (headers, sections, key areas)
        7. extraction_confidence (1-10 score)
        
        Return only valid JSON:
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            metadata_json = response.text.strip()
            # Clean up the response to extract JSON
            if "```json" in metadata_json:
                metadata_json = metadata_json.split("```json")[1].split("```")[0]
            elif "```" in metadata_json:
                metadata_json = metadata_json.split("```")[1].split("```")[0]
            
            return json.loads(metadata_json)
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {"error": str(e), "extraction_confidence": 1}

# Web Scraping Engine
class SkyscraperEngine:
    def __init__(self):
        self.lang_extract = LangExtractProcessor()
    
    async def scrape_with_playwright(self, url: str, anti_detection: bool = True) -> Dict[str, Any]:
        """Advanced web scraping with Playwright"""
        async with async_playwright() as p:
            # Launch browser with anti-detection features
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                ] if anti_detection else []
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                }
            )
            
            page = await context.new_page()
            
            # Add stealth techniques
            if anti_detection:
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)
            
            try:
                # Navigate to page
                await page.goto(str(url), wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(2000)  # Wait for dynamic content
                
                # Extract comprehensive data
                content = await page.content()
                title = await page.title()
                
                # Extract structured data
                page_data = await page.evaluate("""
                    () => {
                        const data = {
                            title: document.title,
                            text: document.body.innerText,
                            links: Array.from(document.querySelectorAll('a')).map(a => ({
                                text: a.innerText.trim(),
                                href: a.href
                            })).filter(l => l.text && l.href),
                            images: Array.from(document.querySelectorAll('img')).map(img => ({
                                src: img.src,
                                alt: img.alt
                            })),
                            tables: Array.from(document.querySelectorAll('table')).map(table => {
                                const rows = Array.from(table.querySelectorAll('tr'));
                                return rows.map(row => 
                                    Array.from(row.querySelectorAll('td, th')).map(cell => cell.innerText.trim())
                                );
                            }),
                            forms: Array.from(document.querySelectorAll('form')).map(form => ({
                                action: form.action,
                                method: form.method,
                                inputs: Array.from(form.querySelectorAll('input')).map(input => ({
                                    name: input.name,
                                    type: input.type,
                                    placeholder: input.placeholder
                                }))
                            })),
                            headings: {
                                h1: Array.from(document.querySelectorAll('h1')).map(h => h.innerText.trim()),
                                h2: Array.from(document.querySelectorAll('h2')).map(h => h.innerText.trim()),
                                h3: Array.from(document.querySelectorAll('h3')).map(h => h.innerText.trim())
                            }
                        };
                        return data;
                    }
                """)
                
                await browser.close()
                return {
                    'success': True,
                    'url': str(url),
                    'raw_html': content,
                    'structured_data': page_data,
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                await browser.close()
                raise Exception(f"Scraping failed: {str(e)}")

    async def process_with_gemini(self, data: Dict[str, Any], instruction: str) -> Dict[str, Any]:
        """Process scraped data with Gemini AI based on user instruction"""
        model = genai.GenerativeModel('gemini-pro')
        
        # Prepare content for AI processing
        content_text = data['structured_data']['text'][:5000]  # Limit for API
        
        prompt = f"""
        User instruction: "{instruction}"
        
        Website data from {data['url']}:
        Title: {data['structured_data']['title']}
        Content: {content_text}
        Links: {len(data['structured_data']['links'])} found
        Tables: {len(data['structured_data']['tables'])} found
        Forms: {len(data['structured_data']['forms'])} found
        
        Based on the user's instruction, extract and return the relevant information in a structured JSON format.
        Focus on what the user specifically asked for.
        """
        
        try:
            response = await model.generate_content_async(prompt)
            ai_response = response.text
            
            # Try to parse as JSON, fallback to structured text
            try:
                if "```json" in ai_response:
                    json_part = ai_response.split("```json")[1].split("```")[0]
                    return json.loads(json_part)
                else:
                    return {"ai_extracted_data": ai_response, "raw_data": data['structured_data']}
            except:
                return {"ai_extracted_data": ai_response, "raw_data": data['structured_data']}
                
        except Exception as e:
            logger.error(f"Gemini processing failed: {e}")
            return {"error": str(e), "raw_data": data['structured_data']}

# Data Export Engine
class DataExporter:
    @staticmethod
    def to_csv(data: Dict) -> str:
        """Convert data to CSV format"""
        if 'raw_data' in data and 'tables' in data['raw_data']:
            # If tables exist, convert to CSV
            all_rows = []
            for table in data['raw_data']['tables']:
                all_rows.extend(table)
            if all_rows:
                df = pd.DataFrame(all_rows)
                return df.to_csv(index=False)
        
        # Fallback: convert key-value pairs to CSV
        df = pd.DataFrame([data])
        return df.to_csv(index=False)
    
    @staticmethod
    def to_json(data: Dict) -> str:
        """Convert data to JSON format"""
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    @staticmethod
    def to_xml(data: Dict) -> str:
        """Convert data to XML format"""
        root = ET.Element("scraped_data")
        
        def dict_to_xml(d, parent):
            for key, value in d.items():
                child = ET.SubElement(parent, str(key))
                if isinstance(value, dict):
                    dict_to_xml(value, child)
                elif isinstance(value, list):
                    for item in value:
                        item_elem = ET.SubElement(child, "item")
                        if isinstance(item, dict):
                            dict_to_xml(item, item_elem)
                        else:
                            item_elem.text = str(item)
                else:
                    child.text = str(value)
        
        dict_to_xml(data, root)
        return ET.tostring(root, encoding='unicode')
    
    @staticmethod
    def to_r_dashboard(data: Dict) -> str:
        """Generate R Shiny dashboard code"""
        r_code = f"""
# SkyScraper.bot Generated R Dashboard
library(shiny)
library(shinydashboard)
library(DT)
library(ggplot2)
library(plotly)

# Data
scraped_data <- '{json.dumps(data, indent=2)}'

# UI
ui <- dashboardPage(
  dashboardHeader(title = "SkyScraper.bot Data Dashboard"),
  dashboardSidebar(
    sidebarMenu(
      menuItem("Overview", tabName = "overview", icon = icon("dashboard")),
      menuItem("Data Table", tabName = "datatable", icon = icon("table")),
      menuItem("Visualizations", tabName = "viz", icon = icon("chart-bar"))
    )
  ),
  dashboardBody(
    tabItems(
      tabItem(tabName = "overview",
        fluidRow(
          box(title = "Data Summary", status = "primary", solidHeader = TRUE, width = 12,
            verbatimTextOutput("summary")
          )
        )
      ),
      tabItem(tabName = "datatable",
        fluidRow(
          box(title = "Scraped Data", status = "primary", solidHeader = TRUE, width = 12,
            DT::dataTableOutput("datatable")
          )
        )
      ),
      tabItem(tabName = "viz",
        fluidRow(
          box(title = "Data Visualization", status = "primary", solidHeader = TRUE, width = 12,
            plotlyOutput("plot")
          )
        )
      )
    )
  )
)

# Server
server <- function(input, output) {{
  output$summary <- renderText({{
    "Data extracted successfully from SkyScraper.bot"
  }})
  
  output$datatable <- DT::renderDataTable({{
    data.frame(Info = "Data extracted successfully")
  }})
  
  output$plot <- renderPlotly({{
    p <- ggplot(data.frame(x = 1:10, y = rnorm(10)), aes(x, y)) +
      geom_line() +
      labs(title = "Sample Visualization", x = "Index", y = "Value")
    ggplotly(p)
  }})
}}

# Run the app
shinyApp(ui = ui, server = server)
"""
        return r_code

# API Routes
@app.post("/api/scrape", response_model=ScrapingResponse)
async def scrape_endpoint(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(verify_google_token)
):
    """Main scraping endpoint"""
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(request.url)) % 10000}"
    
    # Initialize job
    jobs_storage[job_id] = {
        "status": "processing",
        "user_id": user.get("sub"),
        "request": request.dict(),
        "created_at": datetime.now().isoformat()
    }
    
    # Add background task
    background_tasks.add_task(process_scraping_job, job_id, request)
    
    return ScrapingResponse(
        job_id=job_id,
        status="processing"
    )

async def process_scraping_job(job_id: str, request: ScrapingRequest):
    """Background task to process scraping job"""
    try:
        # Initialize scraping engine
        engine = SkyscraperEngine()
        
        # Step 1: Scrape the website
        logger.info(f"Starting scraping for job {job_id}: {request.url}")
        scraped_data = await engine.scrape_with_playwright(str(request.url), request.anti_detection)
        
        # Step 2: Process with Gemini AI
        logger.info(f"Processing with Gemini for job {job_id}")
        processed_data = await engine.process_with_gemini(scraped_data, request.instruction)
        
        # Step 3: Extract metadata with LangExtract approach
        metadata = {}
        if request.extract_metadata:
            logger.info(f"Extracting metadata for job {job_id}")
            content = scraped_data['structured_data']['text']
            metadata = await engine.lang_extract.extract_metadata(content, str(request.url))
        
        # Step 4: Generate exports
        exporter = DataExporter()
        exports = {}
        
        if request.format == "csv":
            exports["csv"] = exporter.to_csv(processed_data)
        elif request.format == "xml":
            exports["xml"] = exporter.to_xml(processed_data)
        elif request.format == "r_dashboard":
            exports["r_dashboard"] = exporter.to_r_dashboard(processed_data)
        else:
            exports["json"] = exporter.to_json(processed_data)
        
        # Update job status
        jobs_storage[job_id].update({
            "status": "completed",
            "data": processed_data,
            "metadata": metadata,
            "exports": exports,
            "completed_at": datetime.now().isoformat()
        })
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        jobs_storage[job_id].update({
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        })

@app.get("/api/jobs/{job_id}", response_model=ScrapingResponse)
async def get_job_status(job_id: str, user: dict = Depends(verify_google_token)):
    """Get job status and results"""
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_storage[job_id]
    
    # Check if user owns this job
    if job.get("user_id") != user.get("sub"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return ScrapingResponse(
        job_id=job_id,
        status=job["status"],
        data=job.get("data"),
        metadata=job.get("metadata"),
        download_urls=job.get("exports", {})
    )

@app.post("/api/auth/google")
async def google_auth(auth_data: UserAuth):
    """Handle Google OAuth authentication"""
    try:
        # Verify token
        idinfo = id_token.verify_oauth2_token(auth_data.token, requests.Request(), GOOGLE_CLIENT_ID)
        
        user_id = idinfo["sub"]
        users_storage[user_id] = {
            "email": auth_data.email,
            "name": auth_data.name,
            "created_at": datetime.now().isoformat(),
            "usage": {"scraped_pages": 0, "api_calls": 0}
        }
        
        return {"status": "success", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/user/usage")
async def get_user_usage(user: dict = Depends(verify_google_token)):
    """Get user usage statistics"""
    user_id = user.get("sub")
    if user_id in users_storage:
        return users_storage[user_id]
    return {"usage": {"scraped_pages": 0, "api_calls": 0}}

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)