import os

from playwright.sync_api import sync_playwright

TEBURIO_URL = "https://app.teburio.de/login"


def login():
    email = os.environ["TEBURIO_EMAIL"]
    password = os.environ["TEBURIO_PASSWORD"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(TEBURIO_URL)
        page.fill("input[type='email']", email)
        page.fill("input[type='password']", password)
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        input("Drücke Enter zum Schließen...")
        browser.close()


if __name__ == "__main__":
    login()
