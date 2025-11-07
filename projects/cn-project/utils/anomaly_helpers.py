import datetime

def check_anomaly_with_cooldown(packets, bytes_count, last_anomaly, normal_intervals):
    """
    Analyze current metrics with cooldown logic to avoid false positives
    after traffic returns to normal.
    
    Args:
        packets (int): Number of packets per second
        bytes_count (int): Number of bytes per second
        last_anomaly (datetime): Timestamp of last anomaly
        normal_intervals (int): Number of consecutive normal intervals
    
    Returns:
        tuple: (is_anomaly: bool, reason: str)
    """
    # Define thresholds
    PACKET_THRESHOLD = 800  # Matching app.py threshold
    BYTES_THRESHOLD = 500000  # Matching app.py threshold
    COOLDOWN_PERIOD = 60  # seconds to wait before allowing new anomalies
    
    # Check for anomalous conditions
    is_anomaly = False
    reason = "Normal traffic pattern"
    
    # If we had a recent anomaly and haven't cooled down, suppress new anomalies
    if last_anomaly:
        last_time = datetime.datetime.fromisoformat(last_anomaly) if isinstance(last_anomaly, str) else last_anomaly
        if (datetime.datetime.now() - last_time).total_seconds() < COOLDOWN_PERIOD:
            return False, "Suppressed (in cooldown period)"
    
    # Check thresholds
    if packets > PACKET_THRESHOLD:
        is_anomaly = True
        reason = f"High packet count: {packets:,} packets/sec"
    elif bytes_count > BYTES_THRESHOLD:
        is_anomaly = True
        reason = f"High traffic volume: {bytes_count:,.0f} bytes/sec"
    
    return is_anomaly, reason