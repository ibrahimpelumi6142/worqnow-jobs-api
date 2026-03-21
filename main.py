"""
WorqNow Jobs API
Multi-country job search API for messaging bots and job applications

Open Source: https://github.com/ibrahimpelumi6142/worqnow-jobs-api
License: MIT
"""

import os
from dotenv import load_dotenv
load_dotenv()
import logging
import re
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Query, HTTPException, Header, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from jobspy import scrape_jobs, Site
import pandas as pd
import io
import csv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - WorqNow API - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="WorqNow Jobs API",
    description="""
Multi-country job search API for messaging bots and job applications.

🌟 Open Source & Free to use
📱 Built for WhatsApp/Telegram job bots
🌍 Global coverage - works in any country

GitHub: https://github.com/ibrahimpelumi6142/worqnow-jobs-api
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Supported job sites from the installed JobSpy version
SUPPORTED_SITES = sorted(site.value for site in Site)

# Special country configurations (only countries with specialized sites)
COUNTRY_SITE_RECOMMENDATIONS = {
    # Middle East - Bayt specialized
    "uae": ["bayt", "google", "indeed", "linkedin", "glassdoor"],
    "united arab emirates": ["bayt", "google", "indeed", "linkedin", "glassdoor"],
    "dubai": ["bayt", "google", "indeed", "linkedin", "glassdoor"],
    "saudi arabia": ["bayt", "google", "indeed", "linkedin", "glassdoor"],
    "qatar": ["bayt", "google", "indeed", "glassdoor"],
    "kuwait": ["bayt", "google", "indeed", "glassdoor"],
    "bahrain": ["bayt", "google", "indeed", "glassdoor"],
    "oman": ["bayt", "google", "indeed", "glassdoor"],

    # India - Naukri specialized
    "india": ["naukri", "google", "indeed", "linkedin", "glassdoor"],

    # USA/Canada - Has ZipRecruiter & Glassdoor
    "usa": ["google", "indeed", "linkedin", "zip_recruiter", "glassdoor"],
    "united states": ["google", "indeed", "linkedin", "zip_recruiter", "glassdoor"],
    "america": ["google", "indeed", "linkedin", "zip_recruiter", "glassdoor"],
    "canada": ["google", "indeed", "linkedin", "glassdoor"],

    # UK - Has Glassdoor
    "uk": ["google", "indeed", "linkedin", "glassdoor"],
    "united kingdom": ["google", "indeed", "linkedin", "glassdoor"],
    "britain": ["google", "indeed", "linkedin", "glassdoor"],
}

# Default sites for ALL other countries (works globally)
DEFAULT_SITES = ["google", "indeed", "linkedin", "glassdoor"]

# Optional API key authentication
ENABLE_AUTH = os.getenv("ENABLE_API_KEY_AUTH", "false").lower() == "true"
API_KEYS = os.getenv("API_KEYS", "").split(",") if ENABLE_AUTH else []
JOBSPY_PROXY = None

# FlareSolverr for bypassing Cloudflare on Google/ZipRecruiter
FLARESOLVERR_URL = os.getenv("FLARESOLVERR_URL", "")

@app.on_event("startup")
async def startup_event():
    """Startup message"""
    logger.info("=" * 60)
    logger.info("🚀 WorqNow Jobs API Starting...")
    logger.info("🌍 Global job search across 50+ countries")
    logger.info("🔍 Job sites: " + ", ".join(SUPPORTED_SITES))
    logger.info(f"Proxy configured: {'YES' if JOBSPY_PROXY else 'NO'}")
    if FLARESOLVERR_URL:
        logger.info(f"FlareSolverr: ENABLED ({FLARESOLVERR_URL})")
    else:
        logger.info("FlareSolverr: DISABLED (Google/ZipRecruiter may not work)")
    
    if ENABLE_AUTH:
        logger.info("🔐 API Key authentication: ENABLED")
    else:
        logger.info("🔓 API Key authentication: DISABLED (open access)")
    
    logger.info("✅ Ready!")
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown message"""
    logger.info("👋 WorqNow Jobs API shutting down...")

# Helper functions
def parse_job_query(query: str) -> Dict[str, Any]:
    """
    Parse natural language job query
    
    Extracts:
    - Job search term
    - Location
    - Remote preference
    
    Examples:
        "web developer in texas usa" -> {"search_term": "web developer", "location": "texas usa", "remote": False}
        "node.js developer in new york" -> {"search_term": "node.js developer", "location": "new york", "remote": False}
        "software engineer" -> {"search_term": "software engineer", "location": None, "remote": False}
        "remote python developer" -> {"search_term": "python developer", "location": None, "remote": True}
    """
    
    original_query = query
    query_lower = query.lower().strip()
    
    result = {
        "search_term": "",
        "location": None,
        "remote": False
    }
    
    # Check for "remote" keyword
    if "remote" in query_lower:
        result["remote"] = True
        query_lower = query_lower.replace("remote", "").strip()
        query = query.replace("remote", "").replace("Remote", "").strip()
    
    # Try to find location with "in" keyword
    location = None
    search_term = query
    
    if " in " in query_lower:
        parts = query.split(" in ", 1)
        if len(parts) == 2:
            search_term = parts[0].strip()
            location = parts[1].strip()
    
    # Clean up "job" or "jobs" from search term
    search_term = re.sub(r'\bjobs?\b', '', search_term, flags=re.IGNORECASE).strip()
    
    # If search term is empty after cleaning, use original
    if not search_term:
        search_term = original_query.replace("remote", "").replace("Remote", "").strip()
        search_term = re.sub(r'\bjobs?\b', '', search_term, flags=re.IGNORECASE).strip()
    
    # Final fallback
    if not search_term:
        search_term = "jobs"
    
    result["search_term"] = search_term
    result["location"] = location
    
    return result

def filter_supported_sites(sites: List[str]) -> List[str]:
    """Keep only sites supported by the installed JobSpy version."""
    filtered = [site for site in sites if site in SUPPORTED_SITES]
    return filtered or DEFAULT_SITES


def get_recommended_sites(location: str) -> List[str]:
    """
    Get recommended job sites for a location
    
    Special countries get specialized sites (Bayt, Naukri, ZipRecruiter, Glassdoor)
    All other countries get global defaults (Google, Indeed, LinkedIn)
    
    This works for ANY country - the defaults work globally!
    """
    if not location:
        return filter_supported_sites(DEFAULT_SITES)
    
    location_lower = location.lower()
    
    # Check if location mentions any special country
    for country, sites in COUNTRY_SITE_RECOMMENDATIONS.items():
        if country in location_lower:
            logger.debug(f"Special country detected: {country} -> {sites}")
            return filter_supported_sites(sites)
    
    # Not a special country - use global sites
    # These work in EVERY country (France, Germany, Japan, Brazil, etc.)
    logger.debug(f"Using default sites for: {location}")
    return filter_supported_sites(DEFAULT_SITES)


def normalize_json_value(value: Any) -> Any:
    """Convert pandas and Python values to JSON-safe primitives."""
    if isinstance(value, dict):
        return {k: normalize_json_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_json_value(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if pd.isna(value):
        return None
    return value

def transform_to_api_format(jobs_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Transform JobSpy DataFrame to API response format
    
    Returns list of job objects with standardized fields
    """
    jobs_list = jobs_df.to_dict('records')
    
    api_jobs = []
    
    for job in jobs_list:
        # Extract location - JobSpy returns a string like "City, State, Country"
        location_raw = job.get('location', '') or ''
        city = country = state = ''
        if isinstance(location_raw, str) and location_raw:
            parts = [p.strip() for p in location_raw.split(',')]
            if len(parts) >= 3:
                city, state, country = parts[0], parts[1], parts[2]
            elif len(parts) == 2:
                city, country = parts[0], parts[1]
            elif len(parts) == 1:
                city = parts[0]
        
        # Extract compensation - JobSpy returns flat columns
        min_salary = job.get('min_amount')
        max_salary = job.get('max_amount')
        currency = job.get('currency')
        _interval = job.get('interval')
        salary_period = 'YEARLY' if not _interval or pd.isna(_interval) else _interval
        
        # Map job type to standard format
        job_type_map = {
            'fulltime': 'FULLTIME',
            'parttime': 'PARTTIME',
            'contract': 'CONTRACT',
            'internship': 'INTERN'
        }
        employment_type = job_type_map.get(
            str(job.get('job_type', '')).lower(),
            'FULLTIME'
        )
        
        # Build standardized job object
        # Build standardized job object
        api_job = {
            'job_id': f"worqnow_{abs(hash(job.get('job_url', '')))}",
            'job_title': normalize_json_value(job.get('title', '')),
            'job_employment_type': employment_type,
            'job_apply_link': normalize_json_value(job.get('job_url', '')),
            'job_description': normalize_json_value(job.get('description', '')),
            'job_is_remote': normalize_json_value(job.get('is_remote', False)),
            'job_posted_at_datetime_utc': normalize_json_value(job.get('date_posted')),
            'job_posted_at_timestamp': None,
            'job_city': normalize_json_value(city),
            'job_state': normalize_json_value(state),
            'job_country': normalize_json_value(country),
            'employer_name': normalize_json_value(job.get('company', '')),
            'employer_logo': normalize_json_value(job.get('company_logo')),
            'employer_website': normalize_json_value(job.get('company_url')),
            'employer_company_type': normalize_json_value(job.get('company_industry')),
            'job_publisher': str(normalize_json_value(job.get('site', 'worqnow'))).title(),
            'job_min_salary': normalize_json_value(min_salary),
            'job_max_salary': normalize_json_value(max_salary),
            'job_salary_currency': normalize_json_value(currency),
            'job_salary_period': normalize_json_value(salary_period.upper() if salary_period else 'YEARLY'),
            'job_apply_is_direct': False,
            'job_apply_quality_score': None,
        }
        
        api_jobs.append(api_job)
    
    return api_jobs

# Optional API key authentication
async def verify_api_key(x_api_key: str = Header(None, alias="x-api-key")):
    """
    Optional API key authentication
    Only enforced if ENABLE_API_KEY_AUTH=true
    """
    if not ENABLE_AUTH:
        return True  # Open access
    
    if not x_api_key:
        raise HTTPException(
            status_code=403,
            detail="API key required. Set API_KEYS in .env for self-hosted deployment."
        )
    
    valid_keys = [k.strip() for k in API_KEYS if k.strip()]
    
    if not valid_keys:
        logger.warning("⚠️  No API keys configured. Set API_KEYS in .env")
        return True  # Allow if no keys configured
    
    if x_api_key not in valid_keys:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    return True

# API Endpoints
@app.get("/", tags=["Info"])
async def root():
    """API information"""
    return {
        "name": "WorqNow Jobs API",
        "version": "1.0.0",
        "description": "Multi-country job search API for messaging bots",
        "github": "https://github.com/ibrahimpelumi6142/worqnow-jobs-api",
        "license": "MIT",
        "authentication": "enabled" if ENABLE_AUTH else "disabled",
        "docs": "/docs",
        "supported_sites": SUPPORTED_SITES,
        "usage": "Self-host this for your own projects. See GitHub README.",
        "example": "GET /api/v1/search?query=web developer in Lagos"
    }

@app.get("/health", tags=["Info"])
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "WorqNow Jobs API",
        "version": "1.0.0"
    }

@app.get("/api/v1/search", tags=["Jobs"])
async def search_jobs(
    # Main parameter
    query: str = Query(
        ...,
        description="Job search query - natural language supported",
        example="software engineer in Lagos"
    ),
    
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    num_pages: int = Query(1, ge=1, le=10, description="Number of pages (10 results per page)"),
    
    # Optional filters
    date_posted: Optional[str] = Query(
        None,
        description="Filter by date posted: all, today, 3days, week, month"
    ),
    remote_jobs_only: Optional[bool] = Query(
        None,
        description="Filter for remote jobs only"
    ),
    employment_types: Optional[str] = Query(
        None,
        description="Employment types (comma-separated): FULLTIME, PARTTIME, CONTRACT, INTERN"
    ),
    
    # Output format
    format: str = Query("json", description="Response format: json or csv"),
    
    # Authentication
    authenticated: bool = Depends(verify_api_key)
):
    """
    Job search endpoint - natural language queries supported
    
    Pass your search in natural language:
    
    Examples:
        ?query=web developer in texas usa
        ?query=node.js developer in new york
        ?query=software engineer in Lagos Nigeria
        ?query=remote python developer
        ?query=accountant in Dubai
        ?query=jobs in Kenya
    
    Works globally - supports ANY country!
    """
    
    try:
        # Parse natural language query
        parsed = parse_job_query(query)
        
        search_term = parsed["search_term"]
        location = parsed["location"]
        is_remote = parsed["remote"]
        
        # Override with explicit parameters if provided
        if remote_jobs_only is not None:
            is_remote = remote_jobs_only
        
        # Smart site selection based on location
        sites = get_recommended_sites(location)
        
        # Map employment types
        job_type = None
        if employment_types:
            type_map = {
                'FULLTIME': 'fulltime',
                'PARTTIME': 'parttime',
                'CONTRACT': 'contract',
                'INTERN': 'internship'
            }
            # Handle comma-separated types (use first one)
            first_type = employment_types.split(',')[0].strip().upper()
            job_type = type_map.get(first_type)
        
        # Map date posted to hours
        hours_old = None
        if date_posted:
            date_map = {
                'today': 24,
                '3days': 72,
                'week': 168,
                'month': 720,
                'all': None
            }
            hours_old = date_map.get(date_posted.lower())
        
        # Calculate results
        results_wanted = 10 * num_pages
        
        logger.info(f"Search: '{query}' -> term='{search_term}', location='{location}', sites={sites}")
        
        # Call JobSpy
        jobs_df = scrape_jobs(
            site_name=sites,
            search_term=search_term,
            location=location or "",
            is_remote=is_remote,
            results_wanted=results_wanted,
            hours_old=hours_old,
            job_type=job_type,
            description_format="markdown",
            verbose=1,
            distance=50,
            proxies=JOBSPY_PROXY,
        )
        
        # Transform to API format
        jobs_data = transform_to_api_format(jobs_df)
        
        # Handle CSV format
        if format.lower() == "csv":
            if not jobs_data:
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["No results found"])
                output.seek(0)
                return StreamingResponse(
                    output,
                    media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=jobs.csv"}
                )
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=jobs_data[0].keys())
            writer.writeheader()
            writer.writerows(jobs_data)
            output.seek(0)
            return StreamingResponse(
                output,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=jobs.csv"}
            )
        
        # Build JSON response
        response = {
            "status": "OK",
            "request_id": f"worqnow_{abs(hash(query + str(page)))}",
            "parameters": {
                "query": query,
                "page": page,
                "num_pages": num_pages
            },
            "data": jobs_data
        }
        
        return JSONResponse(content=normalize_json_value(response))
        
    except Exception as e:
        logger.error(f"❌ Search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Job search failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
