# Python Proxy Server with Real-Time IDS Dashboard

A multi-threaded HTTP/HTTPS proxy server built in Python that includes a signature-based Intrusion Detection System (IDS). All network traffic and security alerts are visualized on a live web dashboard built with Flask and Chart.js.

## ✨ Features

* **HTTP/HTTPS Proxying:** Functions as a standard proxy for web browsing.
* **Multi-Threaded:** Handles multiple client connections simultaneously.
* **Enhanced Intrusion Detection System (IDS):** Inspects plaintext traffic for common web attack patterns like:
    * SQL Injection (SQLi)
    * Cross-Site Scripting (XSS)
    * Local File Inclusion (LFI)
    * Command Injection
    * XXE Injection
    * LDAP Injection
    * Server-Side Request Forgery (SSRF)
* **Live Web Dashboard:** A real-time interface built with Flask that visualizes:
    * Total threats detected and blocked
    * Live alert feed with details of each threat
    * Attack distribution chart
    * Active proxy connections
    * Cache statistics
    * Rate limit monitoring
* **Intelligent Caching:** Caches frequently accessed resources to improve performance
* **Rate Limiting:** Protects against DoS attacks by limiting requests per IP
* **Activity Logging:** Comprehensive logging of all proxy activity
* **Domain Blocking:** Blocks access to a custom list of domains (e.g., facebook.com).
* **Request Anonymization:** Basic modification of outgoing HTTP headers to mask the client's identity.
* **Bandwidth Monitoring:** Tracks total bytes transferred through the proxy

---

## 🔧 Tech Stack

* **Backend:** Python
    * **Sockets:** For low-level networking and proxy functionality.
    * **Threading:** To handle concurrent client connections.
    * **Flask:** To serve the web dashboard and its API.
* **Frontend:**
    * HTML5
    * CSS3
    * JavaScript
* **Charting Library:** [Chart.js](https://www.chartjs.org/) for data visualization.

---

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/hs-2428/Proxy-Server-with-Intrusion-Detection.git
   cd Proxy-Server-with-Intrusion-Detection
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 📖 Usage

1. Run the proxy server:
   ```bash
   python app.py
   ```

2. Configure your browser to use the proxy:
   - Proxy server: `127.0.0.1`
   - Port: `8080`

3. Access the dashboard at: `http://127.0.0.1:5000`

## ⚙️ Configuration

The proxy server can be configured by modifying the constants at the top of `app.py`:

* `LISTEN_PORT` - Port for the proxy server (default: 8080)
* `DASHBOARD_PORT` - Port for the web dashboard (default: 5000)
* `CACHE_ENABLED` - Enable/disable response caching (default: True)
* `RATE_LIMIT_ENABLED` - Enable/disable rate limiting (default: True)
* `MAX_REQUESTS_PER_IP` - Maximum requests per minute per IP (default: 100)
* `BLOCKED_DOMAINS` - Set of domains to block
* `LOG_FILE` - Path to activity log file (default: proxy_activity.log)

## 📊 Dashboard Features

The web dashboard provides real-time monitoring:
* **Statistics Card**: Total requests, threats, cached responses, bandwidth
* **Attack Distribution**: Visual chart showing attack types
* **Live Alerts**: Real-time feed of detected threats
* **Top Domains**: Most visited domains through the proxy
* **Cache Management**: View cache stats and clear cache
* **IP Management**: View and unblock rate-limited IPs

## 📦 Release Package

To create a release package, download the source code and install the dependencies as above.
