import time
import argparse
from botasaurus import Browser

def login_ebay(browser, username, password):
    """ Automates eBay login process """
    browser.go("https://www.ebay.com/signin")

    if browser.exists("#userid"):
        browser.fill("#userid", username)
        browser.click("#signin-continue-btn")

    time.sleep(2)

    if browser.exists("#pass"):
        browser.fill("#pass", password)
        browser.click("#sgnBt")

    time.sleep(3)

    if browser.exists("#passkeys-cancel-btn"):
        browser.click("#passkeys-cancel-btn")

    print("✅ Successfully logged in to eBay")

def start_listing(browser):
    """ Navigates to eBay's selling page and begins a listing """
    browser.go("https://www.ebay.com/sl/sell")
    
    if browser.exists("a[aria-label='Sell']"):
        browser.click("a[aria-label='Sell']")
    
    time.sleep(2)

    if browser.exists(".create-listings-btn"):
        browser.click(".create-listings-btn")

    browser.wait_visible("input[aria-label='Enter brand, model, description, etc.']")
    browser.fill("input[aria-label='Enter brand, model, description, etc.']", "Apple iPhone 12 Pro Max - 256GB - Pacific Blue (Unlocked)")
    browser.press("input[aria-label='Enter brand, model, description, etc.']", "Enter")

    time.sleep(3)
    print("✅ Product title entered.")

def start_automation(username, password):
    """ Runs the automation using user-provided credentials """
    with Browser(headless=False) as browser:
        login_ebay(browser, username, password)
        start_listing(browser)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="eBay Automation CLI")
    parser.add_argument("--username", required=True, help="eBay username/email")
    parser.add_argument("--password", required=True, help="eBay password")
    args = parser.parse_args()

    start_automation(args.username, args.password)