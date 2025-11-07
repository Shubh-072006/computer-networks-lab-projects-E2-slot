// Enhanced dashboard_firewall.c with MAC verification
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <net/if_arp.h>
#include <sys/ioctl.h>

#define PROXY_PORT 5000
#define FLASK_PORT 5001
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
            strcpy(authorized[num_authorized].mac, mac);
            strcpy(authorized[num_authorized].ip, ip);
            strcpy(authorized[num_authorized].name, name);
            num_authorized++;
        }
    }
    fclose(f);
}

// Get MAC address for an IP using ARP
int get_mac_from_ip(const char* ip, char* mac_out) {
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    struct arpreq req;
    struct sockaddr_in *sin;
    
    memset(&req, 0, sizeof(req));
    sin = (struct sockaddr_in *)&req.arp_pa;
    sin->sin_family = AF_INET;
    sin->sin_addr.s_addr = inet_addr(ip);
    strcpy(req.arp_dev, "wlxd03745f84230");
    
    if (ioctl(sock, SIOCGARP, &req) < 0) {
        close(sock);
        return 0;
    }
    
    unsigned char* mac = (unsigned char*)req.arp_ha.sa_data;
    sprintf(mac_out, "%02x:%02x:%02x:%02x:%02x:%02x",
            mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    
    close(sock);
    return 1;
}

// Verify IP-MAC binding
int is_authorized(const char* ip) {
    char actual_mac[18];
    
    // Get actual MAC address from ARP table
    if (!get_mac_from_ip(ip, actual_mac)) {
        printf("⚠️  Could not get MAC for %s\n", ip);
        return 0;
    }
    
    // Check if this IP-MAC combination is authorized
    for (int i = 0; i < num_authorized; i++) {
        if (strcmp(ip, authorized[i].ip) == 0) {
            // IP matches, now check MAC
            if (strcasecmp(actual_mac, authorized[i].mac) == 0) {
                printf("✅ Verified: %s (%s) - %s\n", ip, actual_mac, authorized[i].name);
                return 1;
            } else {
                printf("❌ IP spoofing detected! %s claims to be %s but MAC is %s (expected %s)\n",
                       ip, authorized[i].ip, actual_mac, authorized[i].mac);
                return 0;
            }
        }
    }
    
    printf("❌ Unauthorized IP: %s (MAC: %s)\n", ip, actual_mac);
    return 0;
}

void send_access_denied(int client_sock, const char* client_ip, const char* reason) {
    char response[2048];
    snprintf(response, sizeof(response),
        "HTTP/1.1 403 Forbidden\r\n"
        "Content-Type: text/html\r\n"
        "Connection: close\r\n"
        "\r\n"
        "<!DOCTYPE html>\n"
        "<html><head><title>Access Denied</title>\n"
        "<style>body{font-family:Arial;text-align:center;padding:50px;background:#2c3e50;color:white}\n"
        "h1{color:#e74c3c}.container{background:#34495e;padding:30px;border-radius:10px;max-width:600px;margin:0 auto}</style></head>\n"
        "<body><div class='container'><h1>🚫 Access Denied</h1>\n"
        "<p><strong>%s</strong></p>\n"
        "<p>Your IP: %s</p>\n"
        "<hr><small>Security violations are logged.</small></div></body></html>",
        reason, client_ip);
    
    send(client_sock, response, strlen(response), 0);
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
    
    // Check authorization with MAC verification
    if (!is_authorized(client_ip)) {
        send_access_denied(client_sock, client_ip, 
                          "Your device is not authorized or IP spoofing detected.");
        close(client_sock);
        return NULL;
    }
    
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
    printf("║   Enhanced Dashboard Firewall (MAC Verification) ║\n");
    printf("║   Public Port: 5000 → Flask Port: 5001            ║\n");
    printf("╚═══════════════════════════════════════════════════╝\n\n");
    
    load_authorized();
    printf("📖 Loaded %d authorized devices\n", num_authorized);
    for (int i = 0; i < num_authorized; i++) {
        printf("   ✅ %s ↔ %s (%s)\n", 
               authorized[i].mac, authorized[i].ip, authorized[i].name);
    }
    printf("\n🔒 IP-MAC binding enforcement enabled\n\n");
    
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
    printf("   → Verifying MAC addresses against authorized list\n\n");
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
