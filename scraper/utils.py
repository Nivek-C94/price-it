import statistics


def detect_price_outliers(items):
    """
    Detects price anomalies using a combination of:
    - Interquartile Range (IQR) method with an adaptive multiplier.
    - Modified Z-Score method for better robustness.
    - Mean-based deviation fallback for small datasets.

    Outliers are marked if they are significantly different from the main price range.
    """

    # Extract valid prices from items; prefer 'price_value' if available.
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

    n = len(prices)
    if n < 4:
        # Fallback: Use standard deviation for small datasets
        if n >= 2:
            mean_price = statistics.mean(prices)
            std_dev = statistics.stdev(prices)
            threshold = 1.5 * std_dev  # More aggressive detection

            for item in items:
                try:
                    price_val = item.get("price_value") or float(item["price"].replace("$", "").replace(",", ""))
                    item["outlier"] = abs(price_val - mean_price) > threshold
                except Exception:
                    item["outlier"] = None
        else:
            # Not enough data to detect outliers
            for item in items:
                item["outlier"] = False
        return items

    # Sort prices and calculate IQR
    prices_sorted = sorted(prices)

    def median(data):
        m = len(data)
        if m % 2 == 0:
            return (data[m // 2 - 1] + data[m // 2]) / 2
        else:
            return data[m // 2]

    # Split into quartiles
    mid = n // 2
    Q1 = median(prices_sorted[:mid])
    Q3 = median(prices_sorted[mid + (n % 2):])  # Ignore median in odd cases
    IQR = Q3 - Q1

    # Dynamically adjust the multiplier based on dataset size
    multiplier = 1.5 if n > 10 else 1.2 if n > 5 else 1.0
    lower_bound = Q1 - multiplier * IQR
    upper_bound = Q3 + multiplier * IQR

    # Modified Z-Score Method (for better skew resistance)
    median_price = median(prices_sorted)
    MAD = statistics.median([abs(p - median_price) for p in prices_sorted]) or 1
    z_threshold = 3.5  # Higher sensitivity

    for item in items:
        try:
            price_val = item.get("price_value") or float(item["price"].replace("$", "").replace(",", ""))
            iqr_outlier = (price_val < lower_bound) or (price_val > upper_bound)
            z_score = (0.6745 * (price_val - median_price)) / MAD
            z_outlier = abs(z_score) > z_threshold
            item["outlier"] = iqr_outlier or z_outlier
        except Exception:
            item["outlier"] = None

    return items
