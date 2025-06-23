from fastapi import APIRouter
from web_scrapping.main import run_scraping

router = APIRouter()

@router.get("/run-scraping")
def trigger_scraping():
    return run_scraping()
