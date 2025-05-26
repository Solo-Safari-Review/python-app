import re

# Contains question
def contains_question(text):
    return '?' in text

def contains_number(text):
    if (re.search(r'\d+', str(text))):
        return 1
    else:
        return 0

# Count words
def get_length(text):
    return len(str(text))

# Weekend checker
def is_weekend(input_date):
    if (input_date.weekday() >= 5):
        return 1
    else:
        return 0

def answer_context(context_1, context_2, context_3, context_4):
    if context_1 or context_2 or context_3 or context_4:
        return 1
    else:
        return 0
