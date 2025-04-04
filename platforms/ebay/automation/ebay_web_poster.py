from botasaurus_driver import Driver

from driver import driver_pool


def sanitize_sku(sku):
    """Remove special characters and trim SKU to 50 chars max."""
    import re
    sku = re.sub(r"[^a-zA-Z0-9]", "", sku)
    return sku[:50]


def post_item_stealth(sku, title, price, condition, specifics):
    """Posts an item to eBay via web automation (no API)."""
    bot: Driver = driver_pool.get(timeout=10)
    bot.google_get("https://www.ebay.com/sl/sell")
    bot.wait_for_element("input#title")

    bot.type("input#title", title)
    bot.type("input#price", str(price))
    bot.type("input#sku", sanitize_sku(sku))

    if condition.lower() == "new":
        bot.click("input#condition-new")
    else:
        bot.click("input#condition-used")

    for key, value in specifics.items():
        selector = f"input[name='{key}']"
        bot.type(selector, value)

    bot.click("button#submit-listing")
    bot.wait_for_element("div.success-message")

    return {"success": True, "message": "Item posted successfully via web automation."}

