from scapy.all import sniff
import threading
import logging
class PacketSniffer:
    def __init__(self):
        self.tcp_count = 0
        self.udp_count = 0
        self.running = False

    def sniff_packets(self, update_callback=None):
        # only sniff when running
        def sniffer():
            self.running = True
            self.tcp_count = 0
            self.udp_count = 0
            def packet_callback(packet):
                if packet.haslayer('TCP'):
                    self.tcp_count += 1
                elif packet.haslayer('UDP'):
                    self.udp_count += 1
                if update_callback:
                    update_callback(self.tcp_count, self.udp_count)
            sniff(prn=packet_callback, store=0, stop_filter=lambda x: not self.running)
        thread = threading.Thread(target=sniffer, daemon=True)
        thread.start()
    
    

    def stop_sniffing(self):
        self.running = False
