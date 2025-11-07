import socket
import threading
import time
import random
import re
import sys
import signal
import json
import hashlib
from datetime import datetime
from collections import defaultdict
from flask import Flask, render_template, jsonify, request
import logging

# --- Configuration ---
LISTEN_PORT = 8080
BUFFER_SIZE = 65536
MAX_CONNECTIONS = 200
REQUEST_TIMEOUT = 3.0
DASHBOARD_PORT = 5000
LOG_FILE = "proxy_activity.log"
CACHE_ENABLED = True
RATE_LIMIT_ENABLED = True
MAX_REQUESTS_PER_IP = 100  # Max requests per minute per IP

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Shared State for Dashboard & Proxy ---
stats = {
    "total_threats": 0,
    "blocked_requests": 0,
    "active_connections": 0,
    "total_requests": 0,
    "cached_responses": 0,
    "bytes_transferred": 0,
    "attack_distribution": defaultdict(int),
}
intrusion_logs = []
domain_visits = defaultdict(int)
ip_request_count = defaultdict(lambda: {"count": 0, "timestamp": time.time()})
cache = {}  # Simple in-memory cache
blocked_ips = set()  # IPs that have been rate limited
conn_lock = threading.Lock()

# --- Intrusion Detection System (IDS) ---
class SimpleIDS:
    def __init__(self):
        self.signatures = {
            "SQLi_UNION": re.compile(r"UNION\s+SELECT|SLEEP\(|WAITFOR\s+DELAY", re.IGNORECASE),
            "SQLi_OR_1": re.compile(r"(\'\s*OR\s*\'\d+\'=\'|\s+OR\s+1\s*=\s*1|--|\#)", re.IGNORECASE),
            "XSS_SCRIPT": re.compile(r"<\s*SCRIPT|alert\(|prompt\(|document\.cookie", re.IGNORECASE),
            "XSS_IMG_TAG": re.compile(r"<IMG\s+SRC=[\'\"]javascript:", re.IGNORECASE),
            "LFI_WIN_UNIX": re.compile(r"(\.\.\\){2,}|(\.\./){2,}|/etc/passwd|/etc/shadow", re.IGNORECASE),
            "CMD_INJECTION": re.compile(r"(\|\s*ls|;\s*cat|&&\s*id|&amp;&amp;\s*whoami)", re.IGNORECASE),
            "XXE": re.compile(r"<!ENTITY|<!DOCTYPE.*ENTITY", re.IGNORECASE),
            "LDAP_INJECTION": re.compile(r"\*\)|\(\||\)\(", re.IGNORECASE),
            "SSRF": re.compile(r"(file://|gopher://|dict://|localhost|127\.0\.0\.1|0\.0\.0\.0)", re.IGNORECASE),
        }
        self.categories = {
            "SQLi_UNION": "SQL Injection", "SQLi_OR_1": "SQL Injection",
            "XSS_SCRIPT": "XSS", "XSS_IMG_TAG": "XSS",
            "LFI_WIN_UNIX": "LFI/Path Traversal", "CMD_INJECTION": "Command Injection",
            "XXE": "XXE Injection", "LDAP_INJECTION": "LDAP Injection",
            "SSRF": "SSRF"
        }

    def check_for_intrusion(self, data: bytes) -> tuple[bool, str, str]:
        try:
            data_str = data.decode('utf-8', 'ignore')
        except Exception:
            return False, "Binary data", None
        for name, pattern in self.signatures.items():
            if pattern.search(data_str):
                reason = f"Attack type: {name}"
                category = self.categories.get(name, "Other")
                return True, reason, category
        return False, "Clean", None

IDS_ENGINE = SimpleIDS()

def perform_intrusion_check(data: bytes, source: str) -> bool:
    is_malicious, reason, category = IDS_ENGINE.check_for_intrusion(data)
    if is_malicious:
        log_entry = {
            "id": len(intrusion_logs) + 1,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "severity": random.choice(["Medium", "High", "Critical"]),
            "type": category or "Unknown",
            "source_ip": source.split(' ')[0], # Extract IP
            "status": "Blocked",
            "reason": reason
        }
        with conn_lock:
            intrusion_logs.append(log_entry)
            stats["total_threats"] += 1
            stats["blocked_requests"] += 1
            if category:
                stats["attack_distribution"][category] += 1
        logging.warning(f"INTRUSION DETECTED - {source}: {reason}")
        print(f"🚨 [INTRUSION ALERT - {source}] {reason}")
        return True
    return False

def check_rate_limit(client_ip: str) -> bool:
    """Check if IP has exceeded rate limit"""
    if not RATE_LIMIT_ENABLED:
        return False
    
    if client_ip in blocked_ips:
        return True
    
    with conn_lock:
        current_time = time.time()
        ip_data = ip_request_count[client_ip]
        
        # Reset counter if more than 60 seconds have passed
        if current_time - ip_data["timestamp"] > 60:
            ip_data["count"] = 1
            ip_data["timestamp"] = current_time
        else:
            ip_data["count"] += 1
        
        # Check if limit exceeded
        if ip_data["count"] > MAX_REQUESTS_PER_IP:
            blocked_ips.add(client_ip)
            logging.warning(f"Rate limit exceeded for IP: {client_ip}")
            return True
    
    return False

def get_cached_response(cache_key: str):
    """Retrieve cached response if available"""
    if not CACHE_ENABLED or cache_key not in cache:
        return None
    
    cached_data = cache[cache_key]
    # Check if cache is still valid (5 minutes)
    if time.time() - cached_data["timestamp"] > 300:
        del cache[cache_key]
        return None
    
    with conn_lock:
        stats["cached_responses"] += 1
    return cached_data["response"]

def cache_response(cache_key: str, response: bytes):
    """Cache a response"""
    if CACHE_ENABLED and len(response) < 1024 * 100:  # Only cache responses < 100KB
        cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }

# --- Proxy Server Logic ---
BLOCKED_DOMAINS = {"facebook.com", "youtube.com"}
FAKE_IPS = []  # No hardcoded IPs - configure as needed
FAKE_USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"]

def is_blocked(host):
    """
    Checks if a host or its parent domain is in the blocklist.
    This correctly handles subdomains like 'www.facebook.com'.
    """
    host_only = host.split(':')[0].lower()
    for domain in BLOCKED_DOMAINS:
        if host_only == domain or host_only.endswith('.' + domain):
            return True
    return False

def anonymize_request(request_data: str) -> str:
    lines = request_data.splitlines()
    if not lines: return request_data
    
    headers = {line.split(':', 1)[0].lower(): line.split(':', 1)[1].strip()
               for line in lines[1:] if ':' in line}

    if FAKE_IPS:
        fake_ip = random.choice(FAKE_IPS)
        headers['x-forwarded-for'] = fake_ip
        headers['x-real-ip'] = fake_ip
    headers['user-agent'] = random.choice(FAKE_USER_AGENTS)
    
    for h in ['via', 'x-proxy-id', 'forwarded']: headers.pop(h, None)
    
    new_headers = [f"{k.title()}: {v}" for k, v in headers.items()]
    return '\r\n'.join([lines[0]] + new_headers + ['', ''])

def tunnel_data(source, target):
    try:
        while True:
            data = source.recv(BUFFER_SIZE)
            if not data: break
            target.sendall(data)
    except Exception:
        pass
    finally:
        source.close()
        target.close()

def handle_client(client_socket, addr):
    client_ip = addr[0]
    with conn_lock:
        stats["active_connections"] += 1
        stats["total_requests"] += 1
    
    # Check rate limit
    if check_rate_limit(client_ip):
        client_socket.sendall(b"HTTP/1.1 429 Too Many Requests\r\n\r\nRate limit exceeded.")
        logging.warning(f"Rate limit exceeded for {client_ip}")
        with conn_lock:
            stats["active_connections"] -= 1
        client_socket.close()
        return
    
    try:
        request_data_raw = client_socket.recv(BUFFER_SIZE)
        if not request_data_raw: return

        if perform_intrusion_check(request_data_raw, f"{client_ip} initial request"):
            client_socket.sendall(b"HTTP/1.1 403 Forbidden\r\n\r\nIntrusion Detected.")
            return

        try:
            first_line = request_data_raw.split(b'\n')[0].decode()
            method, url, _ = first_line.split()
        except Exception:
            return

        host_header_match = re.search(rb"Host: ([^\r\n]+)", request_data_raw)
        if not host_header_match: return
        
        host_port = host_header_match.group(1).decode()
        if ':' in host_port:
            webserver, port_str = host_port.split(':')
            port = int(port_str)
        else:
            webserver, port = host_port, (443 if method == "CONNECT" else 80)

        domain_visits[webserver] += 1
        if is_blocked(webserver):
            client_socket.sendall(b"HTTP/1.1 403 Forbidden\r\n\r\nBlocked Domain.")
            logging.info(f"Blocked domain access: {webserver} from {client_ip}")
            return

        # Check cache for GET requests
        cache_key = None
        if method == "GET" and CACHE_ENABLED:
            cache_key = hashlib.md5(f"{webserver}{url}".encode()).hexdigest()
            cached_response = get_cached_response(cache_key)
            if cached_response:
                client_socket.sendall(cached_response)
                logging.info(f"Served cached response for {url}")
                return

        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_socket.connect((webserver, port))

        if method == "CONNECT":
            client_socket.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            
            
            t1 = threading.Thread(target=tunnel_data, args=(client_socket, proxy_socket))
            t2 = threading.Thread(target=tunnel_data, args=(proxy_socket, client_socket))
            t1.daemon = True
            t2.daemon = True
            t1.start()
            t2.start()
            
            
            t1.join()
            t2.join()

        else: 
            anonymized_req = anonymize_request(request_data_raw.decode('latin-1')).encode('latin-1')
            proxy_socket.sendall(anonymized_req)
            
            # Collect response for caching
            if cache_key:
                response_data = b""
                while True:
                    chunk = proxy_socket.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    response_data += chunk
                    client_socket.sendall(chunk)
                    with conn_lock:
                        stats["bytes_transferred"] += len(chunk)
                cache_response(cache_key, response_data)
            else:
                tunnel_data(proxy_socket, client_socket)

        logging.info(f"Request handled: {method} {webserver}{url} from {client_ip}")

    except Exception as e:
        logging.error(f"Error handling client {client_ip}: {e}")
        print(f"[ERROR] {e}")
    finally:
        with conn_lock:
            stats["active_connections"] -= 1
        client_socket.close()

def start_proxy_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', LISTEN_PORT))
    server.listen(MAX_CONNECTIONS)
    print(f"🚀 Proxy server listening on port {LISTEN_PORT}")
    
    while True:
        client_socket, addr = server.accept()
        threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()

# --- Flask Dashboard Web Server ---
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/stats")
def get_stats():
    with conn_lock:
        current_stats = stats.copy()
        current_stats["top_domains"] = sorted(domain_visits.items(), key=lambda x: x[1], reverse=True)[:5]
    return jsonify(current_stats)

@app.route("/api/alerts")
def get_alerts():
    with conn_lock:
        return jsonify(intrusion_logs[-15:])

@app.route("/api/blocked_ips")
def get_blocked_ips():
    """Return list of blocked IPs"""
    with conn_lock:
        return jsonify(list(blocked_ips))

@app.route("/api/cache_stats")
def get_cache_stats():
    """Return cache statistics"""
    with conn_lock:
        return jsonify({
            "cache_size": len(cache),
            "cached_responses": stats["cached_responses"]
        })

@app.route("/api/clear_cache", methods=["POST"])
def clear_cache():
    """Clear the cache"""
    cache.clear()
    logging.info("Cache cleared manually")
    return jsonify({"status": "success", "message": "Cache cleared"})

@app.route("/api/unblock_ip", methods=["POST"])
def unblock_ip():
    """Unblock an IP address"""
    data = request.get_json()
    ip = data.get("ip")
    if ip and ip in blocked_ips:
        blocked_ips.remove(ip)
        logging.info(f"IP unblocked: {ip}")
        return jsonify({"status": "success", "message": f"IP {ip} unblocked"})
    return jsonify({"status": "error", "message": "IP not found"})

if __name__ == "__main__":
    
    proxy_thread = threading.Thread(target=start_proxy_server, daemon=True)
    proxy_thread.start()
    
    
    print(f"📊 Dashboard available at http://127.0.0.1:{DASHBOARD_PORT}")
    app.run(port=DASHBOARD_PORT, debug=False)