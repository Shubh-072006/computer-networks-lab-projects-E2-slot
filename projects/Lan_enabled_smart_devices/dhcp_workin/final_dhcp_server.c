// Custom DHCP Server with MAC-based filtering
// Author: Your Name
// Date: October 2025

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <net/if.h>

#define INTERFACE "wlxd03745f84230"
#define CONFIG_FILE "authorized_devices.txt"

struct dhcp_packet {
    uint8_t op, htype, hlen, hops;
    uint32_t xid;
    uint16_t secs, flags;
    uint32_t ciaddr, yiaddr, siaddr, giaddr;
    uint8_t chaddr[16];
    uint8_t sname[64];
    uint8_t file[128];
    uint32_t magic;
    uint8_t options[312];
} __attribute__((packed));

struct auth_device {
    char mac[18];
    char ip[16];
    char name[64];
} devices[50];
int num_devices = 0;

void load_config() {
    FILE* f = fopen(CONFIG_FILE, "r");
    if (!f) {
        printf("⚠️  No config file found: %s\n", CONFIG_FILE);
        return;
    }
    
    printf("📖 Loading authorized devices:\n");
    char line[256];
    while (fgets(line, sizeof(line), f) && num_devices < 50) {
        char mac[18], ip[16], name[64] = "Unknown";
        int parsed = sscanf(line, "%17s %15s %63s", mac, ip, name);
        if (parsed >= 2 && mac[0] != '#') {
            strcpy(devices[num_devices].mac, mac);
            strcpy(devices[num_devices].ip, ip);
            strcpy(devices[num_devices].name, name);
            printf("   ✅ %s -> %s (%s)\n", mac, ip, name);
            num_devices++;
        }
    }
    fclose(f);
    printf("✅ Loaded %d authorized devices\n\n", num_devices);
}

char* get_ip_for_mac(char* mac) {
    // Check authorized devices
    for (int i = 0; i < num_devices; i++) {
        if (strcasecmp(mac, devices[i].mac) == 0) {
            return devices[i].ip;
        }
    }
    
    // Assign regular IP from pool
    static char ip[16];
    static int counter = 100;
    snprintf(ip, sizeof(ip), "192.168.4.%d", counter++);
    if (counter > 200) counter = 100;
    return ip;
}

int main() {
    printf("\n");
    printf("╔═══════════════════════════════════════════════════╗\n");
    printf("║   Custom DHCP Server with MAC Filtering          ║\n");
    printf("║   Interface: %-36s ║\n", INTERFACE);
    printf("╚═══════════════════════════════════════════════════╝\n\n");
    
    load_config();
    
    // Create socket
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        perror("❌ Socket creation failed");
        return 1;
    }
    
    // Bind to specific interface (CRITICAL!)
    struct ifreq ifr;
    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, INTERFACE, IFNAMSIZ - 1);
    
    if (setsockopt(sock, SOL_SOCKET, SO_BINDTODEVICE, &ifr, sizeof(ifr)) < 0) {
        perror("❌ SO_BINDTODEVICE failed");
        return 1;
    }
    printf("✅ Bound to interface: %s\n", INTERFACE);
    
    // Set socket options
    int opt = 1;
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    setsockopt(sock, SOL_SOCKET, SO_BROADCAST, &opt, sizeof(opt));
    
    // Bind to port 67
    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(67);
    
    if (bind(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("❌ Bind failed");
        return 1;
    }
    
    printf("✅ Listening on UDP port 67\n");
    printf("\n🔄 Waiting for DHCP requests...\n");
    printf("════════════════════════════════════════════════════\n\n");
    
    while (1) {
        struct dhcp_packet request;
        struct sockaddr_in client_addr;
        socklen_t addr_len = sizeof(client_addr);
        
        ssize_t bytes = recvfrom(sock, &request, sizeof(request), 0,
                                (struct sockaddr*)&client_addr, &addr_len);
        
        if (bytes < 0 || ntohl(request.magic) != 0x63825363) continue;
        
        // Parse message type
        uint8_t msg_type = 0;
        for (int i = 0; i < 308 && request.options[i] != 255; ) {
            if (request.options[i] == 53) {
                msg_type = request.options[i + 2];
                break;
            }
            if (request.options[i] == 0) i++;
            else i += 2 + request.options[i + 1];
        }
        
        if (msg_type != 1 && msg_type != 3) continue;
        
        char mac[18];
        snprintf(mac, sizeof(mac), "%02x:%02x:%02x:%02x:%02x:%02x",
                request.chaddr[0], request.chaddr[1], request.chaddr[2],
                request.chaddr[3], request.chaddr[4], request.chaddr[5]);
        
        printf("📨 %s from %s ", 
               msg_type == 1 ? "DISCOVER" : "REQUEST", mac);
        
        char* ip = get_ip_for_mac(mac);
        
        // Build response
        struct dhcp_packet response = {0};
        response.op = 2;
        response.htype = 1;
        response.hlen = 6;
        response.xid = request.xid;
        response.flags = request.flags;
        response.yiaddr = inet_addr(ip);
        response.siaddr = inet_addr("192.168.4.1");
        memcpy(response.chaddr, request.chaddr, 16);
        response.magic = htonl(0x63825363);
        
        int pos = 0;
        response.options[pos++] = 53; response.options[pos++] = 1;
        response.options[pos++] = (msg_type == 1) ? 2 : 5;
        
        response.options[pos++] = 54; response.options[pos++] = 4;
        *(uint32_t*)&response.options[pos] = inet_addr("192.168.4.1"); pos += 4;
        
        response.options[pos++] = 51; response.options[pos++] = 4;
        *(uint32_t*)&response.options[pos] = htonl(86400); pos += 4;
        
        response.options[pos++] = 58; response.options[pos++] = 4;
        *(uint32_t*)&response.options[pos] = htonl(43200); pos += 4;
        
        response.options[pos++] = 59; response.options[pos++] = 4;
        *(uint32_t*)&response.options[pos] = htonl(75600); pos += 4;
        
        response.options[pos++] = 1; response.options[pos++] = 4;
        *(uint32_t*)&response.options[pos] = inet_addr("255.255.255.0"); pos += 4;
        
        response.options[pos++] = 28; response.options[pos++] = 4;
        *(uint32_t*)&response.options[pos] = inet_addr("192.168.4.255"); pos += 4;
        
        response.options[pos++] = 6; response.options[pos++] = 8;
        *(uint32_t*)&response.options[pos] = inet_addr("8.8.8.8"); pos += 4;
        *(uint32_t*)&response.options[pos] = inet_addr("8.8.4.4"); pos += 4;
        
        response.options[pos++] = 3; response.options[pos++] = 4;
        *(uint32_t*)&response.options[pos] = inet_addr("192.168.4.1"); pos += 4;
        
        response.options[pos++] = 255;
        
        // Send
        struct sockaddr_in dest = {0};
        dest.sin_family = AF_INET;
        dest.sin_port = htons(68);
        dest.sin_addr.s_addr = INADDR_BROADCAST;
        
        sendto(sock, &response, sizeof(response), 0,
              (struct sockaddr*)&dest, sizeof(dest));
        
        printf("→ %s: %s\n", 
               msg_type == 1 ? "OFFER" : "ACK", ip);
    }
    
    return 0;
}
