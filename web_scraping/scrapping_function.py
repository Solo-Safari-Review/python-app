from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from web_scraping.prep_func import *

def getUsername(review):
    return review.find_element(By.CLASS_NAME, "d4r55").text

def getSubUserInfo(review):
    try:
        sub_user_info = review.find_element(By.CLASS_NAME, "RfnDt").text
    except NoSuchElementException:
        sub_user_info = None

    is_local_guide = 0
    reviewer_number_of_reviews = 0

    if sub_user_info is not None:
        sub_user_info = sub_user_info.split(" · ")
        is_local_guide = 1 if "Local Guide" in sub_user_info else 0
        if is_local_guide == 1:
            if "ulasan" in sub_user_info[0]:
                reviewer_number_of_reviews = sub_user_info[1].rstrip(' ulasan')
        else:
            if "ulasan" in sub_user_info[0]:
                reviewer_number_of_reviews = sub_user_info[0].rstrip(' ulasan')

    return is_local_guide, reviewer_number_of_reviews

def getRating(review):
    return stars_to_int(review.find_element(By.CLASS_NAME, "kvMYJc").get_attribute("aria-label"))

def getLikes(review):
    return likes_to_int(review.find_elements(By.CLASS_NAME, "pkWtMe"))

def getReviewContexts(review):
    review_contexts_elements = review.find_elements(By.CLASS_NAME, "RfDO5c")

    review_context_1 = review_context_2 = review_context_3 = review_context_4 = None
    if review_contexts_elements:
        for idx, context in enumerate(review_contexts_elements):
            if context.text == "Waktu kunjungan":
                review_context_1 = review_contexts_elements[idx + 1].text
            elif context.text == "Waktu antrean":
                review_context_2 = review_contexts_elements[idx + 1].text
            elif context.text == "Sebaiknya buat reservasi":
                review_context_3 = review_contexts_elements[idx + 1].text
            elif context.text == "Tempat parkir":
                review_context_4 = review_contexts_elements[idx + 1].text

    return review_context_1, review_context_2, review_context_3, review_context_4

def getAnswer(review):
    answer_element = review.find_elements(By.CLASS_NAME, "CDe7pd") or None

    answer = None
    if answer_element:
        # search expand button
        expand_button = answer_element[0].find_elements(By.CSS_SELECTOR, "[aria-label='Lihat lainnya']")
        expand_button[0].click() if expand_button else None
        # get answer
        answer = answer_element[0].find_element(By.CLASS_NAME, "wiI7pd").text

    return answer

def getTime(review):
    time_text_in_review = review.find_element(By.CLASS_NAME, "rsqaWe").text
    if "Diedit" in time_text_in_review:
        time_text_in_review = time_text_in_review.replace("Diedit ", "")
    return time_to_timestamp(time_text_in_review)

def getReviewText(review):
    content_element = review.find_elements(By.CLASS_NAME, "MyEned") or None

    if content_element is not None:
        # expand review
        expand_button = review.find_elements(By.CSS_SELECTOR, "[aria-label='Lihat lainnya']")
        expand_button[0].click() if expand_button else None

        # get review content
        content = content_element[0].find_element(By.CLASS_NAME, "wiI7pd").text
    else:
        content = None

    return content

def getImageCount(review):
    image_count = 0
    image_section = review.find_elements(By.CLASS_NAME, "KtCyie") or None
    if image_section is not None:
        rest_images = image_section[0].find_elements(By.CLASS_NAME, "Tap5If") if image_section[0].find_elements(By.CLASS_NAME, "Tap5If") else None
        if rest_images is not None:
            image_count = 3 + int(rest_images[0].text.lstrip('+'))
        else:
            image_count = len(image_section[0].find_elements(By.CLASS_NAME, "Tya61d"))

    return image_count

def getIsExtremeReview(rating):
    return 1 if rating == 1 or rating == 5 else 0
