from fastapi import FastAPI
from web_scraping.main import run_scraping

app = FastAPI()

@app.get("/run-scraping")
def trigger_scraping():
    return run_scraping()
