import csv, mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "database": "solo-safari-review",
    "user": "root",
    "password": "",
}

def to_csv(data):
    csv_file = open('data.csv', 'w', newline='', encoding="utf-8")
    csv_writer = csv.writer(csv_file, delimiter=';')

    csv_writer.writerow(['username', 'time', 'rating', 'likes', 'content', 'review_context_1', 'review_context_2', 'review_context_3', 'review_context_4', 'answer'])

    for item in data:
        csv_writer.writerow([
            item['username'],
            item['time'],
            item['rating'],
            item['likes'],
            item['content'],
            item['review_context_1'],
            item['review_context_2'],
            item['review_context_3'],
            item['review_context_4'],
            item['answer'],
        ])

    csv_file.close()

def connect_db():
    return mysql.connector.connect(**DB_CONFIG)

# Simpan data ke database
def to_db(data):
    conn = connect_db()
    cursor = conn.cursor()
    query = """
    INSERT INTO reviews (username, likes, content, rating, review_context_1, review_context_2, review_context_3, review_context_4, answer, created_at, answered_any_review_context, review_length, contains_question, contains_number, is_weekend, is_local_guide, reviewer_number_of_reviews, is_extreme_review, raw_content, image_count)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    for review in data:
        cursor.execute(query, (
            review["username"],
            review["likes"],
            review["content"],
            review["rating"],
            review["review_context_1"],
            review["review_context_2"],
            review["review_context_3"],
            review["review_context_4"],
            review["answer"],
            review["time"],
            review["answered_any_review_context"],
            review["review_length"],
            review["contains_question"],
            review["contains_number"],
            review["is_weekend"],
            review["is_local_guide"],
            review["reviewer_number_of_reviews"],
            review["is_extreme_review"],
            review["raw_content"],
            review["image_count"],
        ))

    conn.commit()
    cursor.close()
    conn.close()

