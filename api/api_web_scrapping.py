from fastapi import FastAPI, HTTPException
import subprocess
import sys
import os
import json

app = FastAPI()

# Determine the root directory of the 'python-app'
# This assumes 'api_web_scrapping.py' is in 'python-app/api/'
# So, two 'os.path.dirname' calls will get to 'python-app'
PYTHON_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define the path to the web-scrapping directory and main.py
WEB_SCRAPPING_DIR = os.path.join(PYTHON_APP_DIR, "web-scrapping")
MAIN_SCRIPT_PATH = os.path.join(WEB_SCRAPPING_DIR, "main.py")

@app.post("/run-scraping")
async def run_scraping_script():
    """
    Triggers the web scraping script located in the 'web-scrapping' directory.
    """
    if not os.path.exists(MAIN_SCRIPT_PATH):
        raise HTTPException(status_code=500, detail=f"Scraping script not found at {MAIN_SCRIPT_PATH}")

    if not os.path.isdir(WEB_SCRAPPING_DIR):
        raise HTTPException(status_code=500, detail=f"Web scrapping directory not found at {WEB_SCRAPPING_DIR}")

    try:
        # Ensure the web-scrapping directory is in the Python path for its internal imports
        # This is an alternative to setting cwd and can sometimes be more reliable for imports
        env = os.environ.copy()
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{WEB_SCRAPPING_DIR}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = WEB_SCRAPPING_DIR

        # Execute the main.py script as a subprocess
        # Setting the current working directory (cwd) is crucial for main.py
        # to find its relative imports and any files it might access.
        process = subprocess.Popen(
            [sys.executable, MAIN_SCRIPT_PATH],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=WEB_SCRAPPING_DIR, # Set the working directory
            env=env # Pass the modified environment
        )
        stdout, stderr = process.communicate(timeout=600) # Increased timeout to 10 minutes

        if process.returncode == 0:
            try:
                # Attempt to parse the stdout from main.py as JSON
                scraped_data = json.loads(stdout.decode(errors='ignore'))
                return {
                    "message": "Scraping script executed successfully.",
                    "data": scraped_data # Return the parsed JSON data
                }
            except json.JSONDecodeError:
                # If stdout wasn't valid JSON, return it as raw text like before
                return {
                    "message": "Scraping script executed, but output was not valid JSON.",
                    "output": stdout.decode(errors='ignore')
                }
        else:
            # Log the error for debugging on the server side
            print(f"Error executing script: {stderr.decode(errors='ignore')}")
            print(f"Script output: {stdout.decode(errors='ignore')}")
            raise HTTPException(status_code=500, detail={
                "message": "Scraping script execution failed.",
                "error_details": stderr.decode(errors='ignore'),
                "output": stdout.decode(errors='ignore')
            })
    except subprocess.TimeoutExpired:
        # Log the timeout
        print(f"Scraping script execution timed out after 600 seconds.")
        raise HTTPException(status_code=504, detail="Scraping script execution timed out.")
    except Exception as e:
        # Log the exception
        print(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")



if __name__ == "__main__":
    import uvicorn
    # This assumes you run 'python api_web_scrapping.py' from the 'python-app/api/' directory.
    uvicorn.run(app, host="0.0.0.0", port=8000)
