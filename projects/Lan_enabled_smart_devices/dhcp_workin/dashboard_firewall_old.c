// dashboard_firewall.c - Simple HTTP proxy firewall for Flask
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <pthread.h>

#define PROXY_PORT 5000        // What clients connect to
#define FLASK_PORT 5001        // Move your Flask app to this port
#define CONFIG_FILE "authorized_devices.txt"

struct auth_device {
    char mac[18];
    char ip[16];
    char name[64];
} authorized[50];
int num_authorized = 0;

void load_authorized() {
    FILE* f = fopen(CONFIG_FILE, "r");
    if (!f) return;
    
    char line[256];
    while (fgets(line, sizeof(line), f) && num_authorized < 50) {
        char mac[18], ip[16], name[64] = "Unknown";
        if (sscanf(line, "%17s %15s %63s", mac, ip, name) >= 2 && mac[0] != '#') {
            strcpy(authorized[num_authorized].ip, ip);
            strcpy(authorized[num_authorized].name, name);
            num_authorized++;
        }
    }
    fclose(f);
}

int is_authorized(const char* ip) {
    for (int i = 0; i < num_authorized; i++) {
        if (strcmp(ip, authorized[i].ip) == 0) {
            return 1;
        }
    }
    return 0;
}

void send_access_denied(int client_sock, const char* client_ip) {
    const char* response = 
        "HTTP/1.1 403 Forbidden\r\n"
        "Content-Type: text/html\r\n"
        "Connection: close\r\n"
        "\r\n"
        "<!DOCTYPE html>\n"
        "<html><head><title>Access Denied</title>\n"
        "<style>body{font-family:Arial;text-align:center;padding:50px;background:#f5f5f5}\n"
        "h1{color:#e74c3c}p{color:#555}</style></head>\n"
        "<body><h1>🚫 Access Denied</h1>\n"
        "<p>Your device is not authorized to access this dashboard.</p>\n"
        "<p>Only registered devices can access this resource.</p>\n"
        "<hr><small>Your IP: %s</small></body></html>";
    
    char buffer[2048];
    snprintf(buffer, sizeof(buffer), response, client_ip);
    send(client_sock, buffer, strlen(buffer), 0);
}

void* handle_client(void* arg) {
    int client_sock = *(int*)arg;
    free(arg);
    
    struct sockaddr_in client_addr;
    socklen_t addr_len = sizeof(client_addr);
    getpeername(client_sock, (struct sockaddr*)&client_addr, &addr_len);
    
    char client_ip[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &client_addr.sin_addr, client_ip, INET_ADDRSTRLEN);
    
    printf("📨 Request from %s ", client_ip);
    
    // Check authorization
    if (!is_authorized(client_ip)) {
        printf("❌ BLOCKED\n");
        send_access_denied(client_sock, client_ip);
        close(client_sock);
        return NULL;
    }
    
    printf("✅ ALLOWED\n");
    
    // Forward to Flask
    int flask_sock = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in flask_addr = {0};
    flask_addr.sin_family = AF_INET;
    flask_addr.sin_port = htons(FLASK_PORT);
    flask_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
    
    if (connect(flask_sock, (struct sockaddr*)&flask_addr, sizeof(flask_addr)) < 0) {
        const char* err = "HTTP/1.1 502 Bad Gateway\r\n\r\nFlask app not running";
        send(client_sock, err, strlen(err), 0);
        close(client_sock);
        close(flask_sock);
        return NULL;
    }
    
    // Forward request
    char buffer[4096];
    int bytes = recv(client_sock, buffer, sizeof(buffer), 0);
    if (bytes > 0) {
        send(flask_sock, buffer, bytes, 0);
        
        // Forward response
        while ((bytes = recv(flask_sock, buffer, sizeof(buffer), 0)) > 0) {
            send(client_sock, buffer, bytes, 0);
        }
    }
    
    close(flask_sock);
    close(client_sock);
    return NULL;
}

int main() {
    printf("\n");
    printf("╔═══════════════════════════════════════════════════╗\n");
    printf("║   Dashboard Firewall & Proxy                      ║\n");
    printf("║   Public Port: 5000 → Flask Port: 5001            ║\n");
    printf("╚═══════════════════════════════════════════════════╝\n\n");
    
    load_authorized();
    printf("📖 Loaded %d authorized devices\n", num_authorized);
    for (int i = 0; i < num_authorized; i++) {
        printf("   ✅ %s (%s)\n", authorized[i].ip, authorized[i].name);
    }
    printf("\n");
    
    int server_sock = socket(AF_INET, SOCK_STREAM, 0);
    int opt = 1;
    setsockopt(server_sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    
    struct sockaddr_in server_addr = {0};
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PROXY_PORT);
    
    if (bind(server_sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        perror("bind");
        return 1;
    }
    
    listen(server_sock, 50);
    printf("✅ Firewall listening on 0.0.0.0:%d\n", PROXY_PORT);
    printf("   → Forwarding authorized requests to 127.0.0.1:%d\n\n", FLASK_PORT);
    printf("🔄 Waiting for connections...\n");
    printf("════════════════════════════════════════════════════\n\n");
    
    while (1) {
        int* client_sock = malloc(sizeof(int));
        *client_sock = accept(server_sock, NULL, NULL);
        
        pthread_t thread;
        pthread_create(&thread, NULL, handle_client, client_sock);
        pthread_detach(thread);
    }
    
    return 0;
}
