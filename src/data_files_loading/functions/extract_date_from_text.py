import re
from datetime import datetime

MONTH_MAP = {
    "января": "01", "февраля": "02", "марта": "03", "апреля": "04",
    "мая": "05", "июня": "06", "июля": "07", "августа": "08",
    "сентября": "09", "октября": "10", "ноября": "11", "декабря": "12"
}

DATE_PATTERNS = [
    r'\b(\d{2}\.\d{2}\.\d{4})\b',
    r'\b(\d{4}-\d{2}-\d{2})\b',
    r'\b(\d{2}/\d{2}/\d{4})\b',
    r'\b(\d{1,2}\s+[а-я]+\s+\d{4})\b',
    r'\b(\d{4} г.: на \d{2}\.\d{2})\b'
]


def prepare_date_string(date_str: str) -> str:
    """Вспомогательная функция для замены названия месяца на число"""
    date_str = date_str.lower()
    for month_name, month_num in MONTH_MAP.items():
        if month_name in date_str:
            return date_str.replace(month_name, month_num)
    return date_str


def extract_date_from_text(text: str) -> datetime | None:
    if not text:
        return None

    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)

            if any(c.isalpha() for c in date_str):
                date_str = prepare_date_string(date_str)
                date_str = re.sub(r'\s+', '.', date_str)

            formats = (
                "%d.%m.%Y",
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%d.%m.%Y",
                "%Y г.: на %d.%m"
            )

            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
    return None
