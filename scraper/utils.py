import statistics


def detect_price_outliers(items):
    """
    Detect price anomalies using the IQR method.
    Marks items as outliers if the price is below Q1 - k * IQR or above Q3 + k * IQR.
    The multiplier k is configurable via settings.OUTLIER_IQR_MULTIPLIER (default 1.5).
    """
    # Extract valid prices from items; prefer the 'price_value' if available.
    prices = []
    for item in items:
        try:
            if item.get("price_value") is not None:
                prices.append(item["price_value"])
            elif item.get("price") and item["price"] != "No Price":
                price_val = float(item["price"].replace("$", "").replace(",", ""))
                prices.append(price_val)
        except Exception:
            continue

    if len(prices) < 4:
        # Not enough data to reliably detect outliers; mark all as non-outliers.
        for item in items:
            item["outlier"] = False
        return items

    prices_sorted = sorted(prices)
    n = len(prices_sorted)

    def median(data):
        m = len(data)
        if m % 2 == 0:
            return (data[m // 2 - 1] + data[m // 2]) / 2
        else:
            return data[m // 2]

    # Split data into lower and upper halves
    if n % 2 == 0:
        lower_half = prices_sorted[:n // 2]
        upper_half = prices_sorted[n // 2:]
    else:
        lower_half = prices_sorted[:n // 2]
        upper_half = prices_sorted[n // 2 + 1:]

    Q1 = median(lower_half)
    Q3 = median(upper_half)
    IQR = Q3 - Q1

    # Avoid division by zero or flagging false positives when there's no variability.
    if IQR == 0:
        for item in items:
            item["outlier"] = False
        return items

    try:
        import settings

        multiplier = getattr(settings, "OUTLIER_IQR_MULTIPLIER", 1.5)
    except ImportError:
        multiplier = 1.5

    lower_bound = Q1 - multiplier * IQR
    upper_bound = Q3 + multiplier * IQR

    for item in items:
        try:
            if item.get("price_value") is not None:
                price_val = item["price_value"]
            elif item.get("price") and item["price"] != "No Price":
                price_val = float(item["price"].replace("$", "").replace(",", ""))
            else:
                item["outlier"] = None
                continue

            item["outlier"] = (price_val < lower_bound) or (price_val > upper_bound)
        except Exception:
            item["outlier"] = None

    return items
