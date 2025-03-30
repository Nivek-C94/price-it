from botasaurus import with_page


def sanitize_sku(sku):
    """Remove special characters and trim SKU to 50 chars max."""
    import re
    sku = re.sub(r"[^a-zA-Z0-9]", "", sku)
    return sku[:50]


def post_item_stealth(sku, title, price, condition, specifics):
    """Posts an item to eBay via web automation (no API)."""
    
    @with_page
    def automate_listing(page):
        page.goto("https://www.ebay.com/sl/sell")
        page.wait_for("input#title")

        page.fill("input#title", title)
        page.fill("input#price", str(price))
        page.fill("input#sku", sanitize_sku(sku))

        if condition.lower() == "new":
            page.click("input#condition-new")
        else:
            page.click("input#condition-used")

        for key, value in specifics.items():
            selector = f"input[name='{key}']"
            page.fill(selector, value)

        page.click("button#submit-listing")
        page.wait_for("div.success-message")

        return {"success": True, "message": "Item posted successfully via web automation."}

    return automate_listing()
