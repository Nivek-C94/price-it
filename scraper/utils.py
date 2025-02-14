import statistics

def detect_price_outliers(items):
    """Detect price anomalies based on statistical methods."""
    prices = [float(item["price"].replace("$", "").replace(",", "")) for item in items if item["price"] != "No Price"]
    
    if len(prices) < 2:
        return items  # Not enough data to detect outliers
    
    mean = statistics.mean(prices)
    std_dev = statistics.stdev(prices)
    threshold = 2  # 2 standard deviations away from mean
    
    for item in items:
        try:
            price_value = float(item["price"].replace("$", "").replace(",", ""))
            if abs(price_value - mean) > threshold * std_dev:
                item["outlier"] = True
            else:
                item["outlier"] = False
        except ValueError:
            item["outlier"] = None
    
    return items