
"""
Network Topology Module for Network Monitor
Creates network topology visualizations using NetworkX and Matplotlib
"""

import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import random

class NetworkTopology:
    def __init__(self):
        self.graph = nx.Graph()
        self.device_positions = {}

    def create_topology_from_devices(self, devices):
        """Create network topology from discovered devices"""
        self.graph.clear()

        # Find gateway (usually .1 or first device)
        gateway_ip = None
        for device in devices:
            if device['ip'].endswith('.1') or 'gateway' in device['hostname'].lower():
                gateway_ip = device['ip']
                break

        if not gateway_ip and devices:
            gateway_ip = devices[0]['ip']  # Use first device as gateway

        # Add gateway node
        if gateway_ip:
            self.graph.add_node(gateway_ip, 
                               node_type='gateway',
                               label='Gateway\n' + gateway_ip)

        # Add device nodes and connect to gateway
        for device in devices:
            device_ip = device['ip']
            device_label = f"{device['hostname']}\n{device_ip}"

            if device_ip != gateway_ip:
                self.graph.add_node(device_ip,
                                   node_type='device',
                                   label=device_label,
                                   vendor=device.get('vendor', 'Unknown'))

                # Connect to gateway
                if gateway_ip:
                    self.graph.add_edge(gateway_ip, device_ip)

        return self.graph

    def generate_layout(self, layout_type='spring'):
        """Generate node positions based on layout type"""
        if layout_type == 'spring':
            pos = nx.spring_layout(self.graph, k=2, iterations=50)
        elif layout_type == 'circular':
            pos = nx.circular_layout(self.graph)
        elif layout_type == 'shell':
            pos = nx.shell_layout(self.graph)
        elif layout_type == 'random':
            pos = nx.random_layout(self.graph)
        else:
            pos = nx.spring_layout(self.graph)

        self.device_positions = pos
        return pos

    def create_matplotlib_figure(self, layout_type='spring', figsize=(12, 8)):
        """Create matplotlib figure with network topology"""
        if not self.graph.nodes():
            return None

        # Create figure
        fig = Figure(figsize=figsize, dpi=100, facecolor='white')
        ax = fig.add_subplot(111)

        # Generate layout
        pos = self.generate_layout(layout_type)

        # Separate nodes by type
        gateway_nodes = [n for n, d in self.graph.nodes(data=True) 
                        if d.get('node_type') == 'gateway']
        device_nodes = [n for n, d in self.graph.nodes(data=True) 
                       if d.get('node_type') == 'device']

        # Draw nodes
        nx.draw_networkx_nodes(self.graph, pos, 
                              nodelist=gateway_nodes,
                              node_color='#e74c3c',  # Red for gateway
                              node_size=1200,
                              alpha=0.9,
                              ax=ax)

        nx.draw_networkx_nodes(self.graph, pos,
                              nodelist=device_nodes,
                              node_color='#3498db',  # Blue for devices
                              node_size=800,
                              alpha=0.8,
                              ax=ax)

        # Draw edges
        nx.draw_networkx_edges(self.graph, pos,
                              edge_color='#95a5a6',
                              alpha=0.6,
                              width=2,
                              ax=ax)

        # Draw labels
        labels = {node: data.get('label', node) 
                 for node, data in self.graph.nodes(data=True)}
        nx.draw_networkx_labels(self.graph, pos,
                               labels=labels,
                               font_size=8,
                               font_weight='bold',
                               ax=ax)

        # Set title and remove axes
        ax.set_title(f"Network Topology ({len(self.graph.nodes())} devices)", 
                    fontsize=14, fontweight='bold', pad=20)
        ax.axis('off')

        # Add legend
        gateway_patch = plt.Line2D([0], [0], marker='o', color='w', 
                                  markerfacecolor='#e74c3c', markersize=15, label='Gateway')
        device_patch = plt.Line2D([0], [0], marker='o', color='w', 
                                 markerfacecolor='#3498db', markersize=12, label='Devices')
        ax.legend(handles=[gateway_patch, device_patch], loc='upper right')

        return fig

    def get_network_stats(self):
        """Get basic network statistics"""
        if not self.graph.nodes():
            return {}

        return {
            'total_devices': len(self.graph.nodes()),
            'total_connections': len(self.graph.edges()),
            'network_density': nx.density(self.graph),
            'connected_components': nx.number_connected_components(self.graph)
        }
