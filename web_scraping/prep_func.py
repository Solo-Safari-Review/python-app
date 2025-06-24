from datetime import datetime
import dateparser

def time_to_timestamp(time):
    if isinstance(time, list):
        times = []
        for item in time:
            times.append(dateparser.parse(item if isinstance(item, str) else item.text))
        return times

    else:
        return dateparser.parse(time)

stars_to_int = lambda stars: int(stars.split()[0])
likes_to_int = lambda likes_elements: likes_elements[0].text if likes_elements else 0

def json_datetime_converter(o):
    if isinstance(o, datetime):
        return o.isoformat() # Convert datetime to ISO 8601 string format
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")
