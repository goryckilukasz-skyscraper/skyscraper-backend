# Lightweight SkyScraper Backend - Replace your scraping engine with this

import os
import json
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import aiohttp
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, HttpUrl
import google.generativeai as genai
import pandas as pd
import xml.etree.ElementTree as ET
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import re
from urllib.parse import urljoin, urlparse

# Configuration
GOOGLE_CLIENT_ID = "416380249965-ljohffe5opnfb3v52ehkq03svdogk99i.apps.googleusercontent.com"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCbVtyxS4f6ZWU8ceHm6wHEvEfi-2DA5Ag")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Initialize FastAPI
app = FastAPI(
    title="SkyScraper.bot API", 
    version="1.0.0",
    description="Lightweight web scraping with AI-powered extraction"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://skyscraper.bot",
        "https://www.skyscraper.bot",
        "http://localhost:3000"
    ] if ENVIRONMENT == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models
class ScrapingRequest(BaseModel):
    url: HttpUrl
    instruction: str
    format: str = "json"
    timeout: Optional[int] = 30

class ScrapingResponse(BaseModel):
    job_id: str
    status: str
    data: Optional[Dict] = None
    metadata: Optional[Dict] = None
    download_urls: Optional[Dict] = None
    processing_time: Optional[float] = None
    message: Optional[str] = None

# Storage
jobs_storage = {}
users_storage = {}

# Lightweight Web Scraper
class LightweightScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    async def scrape_url(self, url: str, timeout: int = 30) -> Dict[str, Any]:
        """Lightweight web scraping using requests + BeautifulSoup"""
        try:
            logger.info(f"Scraping: {url}")
            
            # Make request
            response = self.session.get(str(url), timeout=timeout, allow_redirects=True)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract data
            data = {
                'url': str(url),
                'title': soup.title.string if soup.title else 'No title',
                'text': soup.get_text(strip=True, separator=' '),
                'html': str(soup),
                'meta': self._extract_meta(soup),
                'links': self._extract_links(soup, url),
                'images': self._extract_images(soup, url),
                'headings': self._extract_headings(soup),
                'tables': self._extract_tables(soup),
                'forms': self._extract_forms(soup),
                'lists': self._extract_lists(soup)
            }
            
            return {
                'success': True,
                'url': str(url),
                'structured_data': data,
                'timestamp': datetime.now().isoformat(),
                'scraping_stats': {
                    'content_length': len(data['text']),
                    'links_found': len(data['links']),
                    'images_found': len(data['images']),
                    'tables_found': len(data['tables']),
                    'forms_found': len(data['forms'])
                }
            }
            
        except requests.RequestException as e:
            logger.error(f"Scraping failed for {url}: {str(e)}")
            raise Exception(f"Failed to scrape {url}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {str(e)}")
            raise Exception(f"Scraping error: {str(e)}")
    
    def _extract_meta(self, soup) -> Dict[str, str]:
        """Extract meta information"""
        meta = {}
        for tag in soup.find_all('meta'):
            name = tag.get('name') or tag.get('property')
            content = tag.get('content')
            if name and content:
                meta[name] = content
        return meta
    
    def _extract_links(self, soup, base_url: str) -> List[Dict[str, str]]:
        """Extract all links"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            if href and text:
                # Make absolute URL
                absolute_url = urljoin(base_url, href)
                links.append({
                    'text': text,
                    'href': absolute_url,
                    'title': link.get('title', '')
                })
        return links[:100]  # Limit to first 100 links
    
    def _extract_images(self, soup, base_url: str) -> List[Dict[str, str]]:
        """Extract all images"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                absolute_url = urljoin(base_url, src)
                images.append({
                    'src': absolute_url,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                })
        return images[:50]  # Limit to first 50 images
    
    def _extract_headings(self, soup) -> Dict[str, List[str]]:
        """Extract all headings"""
        headings = {}
        for i in range(1, 7):  # h1 to h6
            tag_name = f'h{i}'
            headings[tag_name] = [h.get_text(strip=True) for h in soup.find_all(tag_name)]
        return headings
    
    def _extract_tables(self, soup) -> List[Dict[str, Any]]:
        """Extract table data"""
        tables = []
        for table in soup.find_all('table'):
            rows = []
            headers = []
            
            # Get headers
            header_row = table.find('tr')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            
            # Get all rows
            for row in table.find_all('tr')[1:]:  # Skip header row
                cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            
            if headers or rows:
                tables.append({
                    'headers': headers,
                    'rows': rows[:20]  # Limit rows
                })
        
        return tables[:10]  # Limit to first 10 tables
    
    def _extract_forms(self, soup) -> List[Dict[str, Any]]:
        """Extract form information"""
        forms = []
        for form in soup.find_all('form'):
            inputs = []
            for input_tag in form.find_all(['input', 'select', 'textarea']):
                inputs.append({
                    'name': input_tag.get('name', ''),
                    'type': input_tag.get('type', ''),
                    'placeholder': input_tag.get('placeholder', ''),
                    'required': input_tag.has_attr('required')
                })
            
            forms.append({
                'action': form.get('action', ''),
                'method': form.get('method', 'GET'),
                'inputs': inputs
            })
        
        return forms[:5]  # Limit to first 5 forms
    
    def _extract_lists(self, soup) -> List[Dict[str, Any]]:
        """Extract list data"""
        lists = []
        for list_tag in soup.find_all(['ul', 'ol']):
            items = [li.get_text(strip=True) for li in list_tag.find_all('li')]
            if items:
                lists.append({
                    'type': list_tag.name,
                    'items': items[:20]  # Limit items
                })
        
        return lists[:10]  # Limit to first 10 lists

# Enhanced LangExtract (same as before)
class LightweightLangExtract:
    def __init__(self, api_key: str):
        self.model = genai.GenerativeModel('gemini-pro')
        self.api_key = api_key
    
    async def smart_extract(self, content: str, instruction: str, url: str) -> Dict[str, Any]:
        """Smart extraction with AI"""
        start_time = time.time()
        
        try:
            # Limit content for API
            limited_content = content[:6000]
            
            # Create extraction prompt
            prompt = f"""
            Extract information based on this instruction: "{instruction}"
            
            From website: {url}
            Content: {limited_content}
            
            Based on the user's instruction, extract the relevant information in JSON format.
            Focus on what the user specifically requested.
            Structure your response appropriately for the type of data requested.
            
            Return only valid JSON.
            """
            
            # Get AI response
            response = await self.model.generate_content_async(prompt)
            ai_response = response.text
            
            # Clean and parse JSON
            try:
                if "```json" in ai_response:
                    json_part = ai_response.split("```json")[1].split("```")[0]
                    extracted_data = json.loads(json_part)
                else:
                    # Try to parse as-is
                    extracted_data = json.loads(ai_response)
            except json.JSONDecodeError:
                # Fallback to structured text
                extracted_data = {
                    "ai_extracted_content": ai_response,
                    "note": "AI response could not be parsed as JSON"
                }
            
            processing_time = time.time() - start_time
            
            return {
                "extracted_data": extracted_data,
                "metadata": {
                    "url": url,
                    "instruction": instruction,
                    "processing_time": processing_time,
                    "extraction_method": "lightweight_ai"
                },
                "confidence": 8.0  # High confidence for AI extraction
            }
            
        except Exception as e:
            logger.error(f"AI extraction failed: {str(e)}")
            return {
                "error": str(e),
                "extracted_data": {},
                "metadata": {"processing_time": time.time() - start_time}
            }

# Lightweight Engine
class LightweightEngine:
    def __init__(self):
        self.scraper = LightweightScraper()
        self.lang_extract = LightweightLangExtract(GEMINI_API_KEY)
    
    async def process_request(self, url: str, instruction: str, timeout: int = 30) -> Dict[str, Any]:
        """Process scraping request"""
        try:
            # Step 1: Scrape the website
            scraped_data = await asyncio.get_event_loop().run_in_executor(
                None, self.scraper.scrape_url, url, timeout
            )
            
            # Step 2: Extract with AI
            content = scraped_data['structured_data']['text']
            ai_result = await self.lang_extract.smart_extract(content, instruction, url)
            
            # Step 3: Combine results
            result = {
                "scraped_data": scraped_data['structured_data'],
                "ai_extracted": ai_result['extracted_data'],
                "metadata": {
                    **scraped_data.get('scraping_stats', {}),
                    **ai_result['metadata'],
                    "timestamp": scraped_data['timestamp']
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            raise e

# Data Export (same as before)
class DataExporter:
    @staticmethod
    def to_csv(data: Dict) -> str:
        df = pd.DataFrame([data])
        return df.to_csv(index=False)
    
    @staticmethod
    def to_json(data: Dict) -> str:
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    @staticmethod
    def to_xml(data: Dict) -> str:
        root = ET.Element("scraped_data")
        def dict_to_xml(d, parent):
            for key, value in d.items():
                child = ET.SubElement(parent, str(key).replace(' ', '_'))
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

# API Routes
@app.post("/api/scrape", response_model=ScrapingResponse)
async def scrape_endpoint(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """Main scraping endpoint"""
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(request.url)) % 10000}"
    
    jobs_storage[job_id] = {
        "status": "processing",
        "request": request.dict(),
        "created_at": datetime.now().isoformat()
    }
    
    background_tasks.add_task(process_lightweight_job, job_id, request)
    
    return ScrapingResponse(
        job_id=job_id,
        status="processing",
        message="Scraping job started"
    )

async def process_lightweight_job(job_id: str, request: ScrapingRequest):
    """Process scraping job with lightweight engine"""
    try:
        engine = LightweightEngine()
        
        logger.info(f"Starting lightweight scraping for job {job_id}")
        result = await engine.process_request(str(request.url), request.instruction, request.timeout)
        
        # Generate exports
        exporter = DataExporter()
        exports = {}
        
        if request.format == "csv":
            exports["csv"] = exporter.to_csv(result)
        elif request.format == "xml":
            exports["xml"] = exporter.to_xml(result)
        else:
            exports["json"] = exporter.to_json(result)
        
        jobs_storage[job_id].update({
            "status": "completed",
            "data": result,
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
async def get_job_status(job_id: str):
    """Get job status and results"""
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_storage[job_id]
    
    return ScrapingResponse(
        job_id=job_id,
        status=job["status"],
        data=job.get("data"),
        download_urls=job.get("exports", {}),
        message=job.get("error") if job["status"] == "failed" else None
    )

# Test endpoint (no auth required)
@app.post("/api/test-scrape")
async def test_scrape(url: str, instruction: str = "Extract main content"):
    """Quick test endpoint"""
    try:
        engine = LightweightEngine()
        result = await engine.process_request(url, instruction, 15)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0-lightweight",
        "features": ["lightweight_scraping", "ai_extraction", "multi_format_export"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
