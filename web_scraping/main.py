# web-scrapping/main.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from datetime import datetime
from web_scraping.prep_func import *
from web_scraping.save import to_db
from web_scraping.get_attributes import *
from web_scraping.scrapping_function import *
from web_scraping.preprocessing import *
import joblib, os, mysql.connector
import pandas as pd
from dotenv import load_dotenv
import tempfile
import shutil
load_dotenv()


def run_scraping():
    try:
        # Setup path
        PYTHON_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        MODELS_DIR = os.path.join(PYTHON_APP_DIR, "models")
        PREDICT_HELPFUL_DIR = os.path.join(MODELS_DIR, "predict-helpful")
        PREDICT_RATING_DIR = os.path.join(MODELS_DIR, "predict-rating")

        # Load model
        rating_xgb_model = joblib.load(os.path.join(PREDICT_RATING_DIR, "rating_xgboost.pkl"))
        helpful_model = joblib.load(os.path.join(PREDICT_HELPFUL_DIR, "model_helpfulness_final.pkl"))

        driver = None
        # tmp_profile = tempfile.mkdtemp()

        # Headless options
        options = webdriver.ChromeOptions()

        options.binary_location = "/usr/bin/google-chrome"
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        # options.add_argument(f'--user-data-dir={tmp_profile}')

        service = Service("/usr/bin/chromedriver")

        try:
            print('Initializing Chrome driver with temporary profile...')
            driver = webdriver.Chrome(service=service, options=options)
            # driver = webdriver.Chrome(options=options)
            maps_url = f"https://www.google.com/maps/search/solo+safari/"
            driver.get(maps_url)

            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Ulasan')]"))
            ).click()

            # Tunggu dan klik tombol urutkan
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Urutkan')]"))
            ).click()

            # Tunggu menu muncul dan klik "Terbaru"
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "action-menu"))
            )
            menu_button = driver.find_element(By.ID, "action-menu")
            menu_button.find_element(By.CSS_SELECTOR, "[data-index='1']").click()

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "jJc9Ad"))
            )
            print('Chrome driver initialized and navigated to reviews page.')

            # Ambil timestamp terakhir dari DB
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD")
            )
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM reviews ORDER BY id DESC LIMIT 1")
            last_data = cursor.fetchone()
            cursor.close()
            conn.close()

            if last_data:
                target_timestamp = last_data['created_at'].replace(minute=0, second=0, microsecond=0)
                last_username = last_data['username']
            else:
                target_timestamp = time_to_timestamp("1 hari lalu")
                last_username = ""

            before_timestamp = datetime.now()
            on_target = False
            frame = driver.find_element(By.CLASS_NAME, "DxyBCb")
            scroll_origin = ScrollOrigin.from_element(frame, 0, 0)
            target_found = False
            print('Starting to scroll and collect reviews...')

            # Scroll dan kumpulkan review
            while not on_target:
                while not target_found:
                    ActionChains(driver).scroll_from_origin(scroll_origin, 0, 1500).perform()
                    time_list = driver.find_elements(By.CLASS_NAME, "rsqaWe");
                    cleaned_time_list = []
                    for time in time_list:
                        if "Diedit" in time.text:
                            cleaned_time = time.text.replace("Diedit ", "")
                            cleaned_time_list.append(cleaned_time)
                        else:
                            cleaned_time_list.append(time.text)
                    times = time_to_timestamp(cleaned_time_list)
                    if any(time < target_timestamp for time in times):
                        target_found = True
                        print('Target timestamp found, collecting reviews...')

                reviews = driver.find_elements(By.CLASS_NAME, "jJc9Ad")
                data_reviews = []

                for idx, review in enumerate(reviews):
                    time_ = times[idx]
                    if time_ >= before_timestamp: continue
                    if time_ < target_timestamp: on_target = True; break
                    content = getReviewText(review)
                    if not content: continue  # skip if no content
                    raw_content = content
                    username = getUsername(review)
                    is_local_guide, reviewer_number_of_reviews = getSubUserInfo(review)
                    rating = getRating(review)
                    likes = getLikes(review)
                    image_count = getImageCount(review)
                    rc1, rc2, rc3, rc4 = getReviewContexts(review)
                    answer = getAnswer(review)
                    is_extreme = getIsExtremeReview(rating)

                    data_reviews.append({
                        "username": username,
                        "time": time_,
                        "rating": rating,
                        "content": content,
                        "likes": likes,
                        "review_context_1": rc1,
                        "review_context_2": rc2,
                        "review_context_3": rc3,
                        "review_context_4": rc4,
                        "answer": answer,
                        "is_local_guide": is_local_guide,
                        "reviewer_number_of_reviews": reviewer_number_of_reviews,
                        "image_count": image_count,
                        "is_extreme_review": is_extreme,
                        "raw_content": raw_content
                    })

            print('Finished collecting reviews, processing data...')

            # filter berdasarkan username terakhir
            if last_username:
                filtered = []
                passed_last = False
                for r in data_reviews:
                    if r['username'] == last_username:
                        passed_last = True
                        continue
                    if passed_last is False:
                        filtered.append(r)
                data_reviews = filtered

            data_reviews.reverse()

            # preprocessing dan fitur tambahan
            for item in data_reviews:
                item['content'] = preprocessing(item['content'])
                item['answered_any_review_context'] = answer_context(
                    item['review_context_1'], item['review_context_2'],
                    item['review_context_3'], item['review_context_4']
                )
                item['contains_question'] = contains_question(item['content'])
                item['contains_number'] = contains_number(item['content'])
                item['review_length'] = get_length(item['content'])
                item['is_weekend'] = is_weekend(item['time'])

                try:
                    helpful_data = pd.DataFrame([{
                        'stars': item['rating'],
                        'review_length': item['review_length'],
                        'image_count': item['image_count'],
                        'review_age_days': (datetime.now() - item['time']).days,
                        'is_extreme_rating': item['is_extreme_review'],
                        'is_weekend': item['is_weekend'],
                        'reviewerNumberOfReviews': item['reviewer_number_of_reviews'],
                    }])
                    item['is_helpful'] = int(helpful_model.predict(helpful_data)[0])
                except:
                    item['is_helpful'] = 0

            print('Data processing complete, preparing to save to database...')
            if data_reviews:
                to_db(data_reviews)
                return {
                    "status": "success",
                    "total_reviews": len(data_reviews),
                }
            else:
                return {
                    "status": "error",
                    "message": "Tidak ada review baru yang ditemukan.",
                }

        except Exception as e:
            if driver:
                ERROR_PATH = os.path.join(PYTHON_APP_DIR, "error_logs")
                if not os.path.exists(ERROR_PATH):
                    os.makedirs(ERROR_PATH)
                driver.save_screenshot(os.path.join(ERROR_PATH, f"error_screenshot{datetime.now().strftime('%Y%m%d%H%M%S')}.png"))

        finally:
            print("Cleaning up temporary profile...")
            if driver:
                driver.quit()
            # shutil.rmtree(tmp_profile, ignore_errors=True)

    except Exception as e:
        return {"status": "error", "message": str(e)}
