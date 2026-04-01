from datetime import datetime

from playwright.sync_api import Locator

from src.data_files_loading.functions.extract_date_from_text import extract_date_from_text


def get_date_from_referenceable(locator: Locator) -> datetime | None:
    locator = locator.locator("xpath=../../../../..").locator(".document-regular_date")
    date_str = locator.text_content()
    date = extract_date_from_text(date_str)
    return date


def get_date_from_versions_item(locator: Locator) -> datetime | None:
    date_str = locator.get_attribute("data-tooltip-content")
    date = extract_date_from_text(date_str)
    return date