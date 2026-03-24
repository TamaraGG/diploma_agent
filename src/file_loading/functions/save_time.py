import datetime

TIME_LOG_FILE = "time_log.txt"

def save_time():
    with open(TIME_LOG_FILE, "a", encoding="utf-8") as text_file:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text_file.write(f"\nпоследнее извлечение данных: {current_time}")