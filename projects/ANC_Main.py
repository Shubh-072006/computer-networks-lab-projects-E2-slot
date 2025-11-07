#
# Ant Colony Optimization for Dynamic Route Finding
#
# This script simulates finding the best path in a network using an Ant Colony
# Optimization (ACO) algorithm. It considers dynamic "traffic" which affects
# path costs over time. The result is compared with the static shortest path
# found by Dijkstra's algorithm.
#

import networkx as nx
import random
import matplotlib.pyplot as plt

# --- 1. Network Generation ---

def generate_traffic_network(num_nodes=15, edge_probability=0.2, min_weight=1, max_weight=10):
    """
    Generates a random, weakly-connected directed graph representing a traffic network.

    Each edge is assigned a 'weight' (base travel time) and initialized with
    'pheromone' and 'current_traffic' attributes for the ACO algorithm.

    Args:
        num_nodes (int): The number of nodes (intersections) in the network.
        edge_probability (float): The probability of an edge existing between any two nodes.
        min_weight (int): The minimum possible weight for an edge.
        max_weight (int): The maximum possible weight for an edge.

    Returns:
        nx.DiGraph: A NetworkX directed graph representing the network.
    """
    # Generate a random graph based on the Erdos-Renyi model
    G = nx.fast_gnp_random_graph(n=num_nodes, p=edge_probability, seed=42, directed=True)

    # Ensure the graph is weakly connected so a path is likely to exist.
    # This loop connects any isolated components to the main part of the graph.
    if not nx.is_weakly_connected(G):
        components = list(nx.weakly_connected_components(G))
        main_component = components[0]
        for component in components[1:]:
            # Pick a random node from each component to connect them
            node_from_main = random.choice(list(main_component))
            node_from_component = random.choice(list(component))
            G.add_edge(node_from_main, node_from_component)
            main_component.update(component)

    # Initialize edge attributes for the ACO simulation
    initial_pheromone = 1.0
    for u, v in G.edges():
        G.edges[u, v]['weight'] = random.randint(min_weight, max_weight)
        G.edges[u, v]['pheromone'] = initial_pheromone
        G.edges[u, v]['current_traffic'] = 0  # Represents accumulated congestion

    return G


# --- 2. Ant Colony Optimization Algorithm ---

class AntColonyOptimization:
    """
    Implements the Ant Colony Optimization algorithm to find the optimal path
    in a graph, considering dynamic traffic conditions.
    """
    def __init__(self, graph, start_node, end_node, num_ants, num_iterations,
                 alpha, beta, rho, Q, q0, elitist_weight):
        """
        Initializes the ACO solver with its parameters.

        Args:
            graph (nx.DiGraph): The network graph to traverse.
            start_node (int): The starting node for the ants.
            end_node (int): The destination node for the ants.
            num_ants (int): The number of ants in the colony.
            num_iterations (int): The number of iterations to run the algorithm.
            alpha (float): The pheromone influence factor (τ^α).
            beta (float): The heuristic influence factor (η^β).
            rho (float): The pheromone evaporation rate (0 < ρ ≤ 1).
            Q (float): The pheromone deposit amount constant.
            q0 (float): The exploration vs. exploitation trade-off factor.
            elitist_weight (float): The reinforcement weight for the best-so-far path.
        """
        self.G = graph
        self.start = start_node
        self.end = end_node
        self.num_ants = num_ants
        self.max_iterations = num_iterations
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.Q = Q
        self.q0 = q0
        self.elitist_weight = elitist_weight

        self.best_path = None
        self.best_cost = float('inf')
        self.cost_history = []
        self.sample_paths_for_plot = {} # Stores paths at key iterations for visualization

    def _get_dynamic_cost(self, u, v):
        """Calculates the cost of an edge, including a penalty for traffic."""
        base_cost = self.G.edges[u, v]['weight']
        traffic_penalty = 0.1 * self.G.edges[u, v].get('current_traffic', 0)
        return base_cost + traffic_penalty

    def _get_heuristic_value(self, u, v):
        """Calculates the heuristic desirability of an edge (inverse of cost)."""
        cost = self._get_dynamic_cost(u, v)
        return 1.0 / cost if cost > 0 else float('inf')

    def _select_next_node(self, current_node, visited_nodes):
        """Selects the next node for an ant based on pheromones and heuristics."""
        neighbors = [v for v in self.G.neighbors(current_node) if v not in visited_nodes]
        if not neighbors:
            return None

        attractiveness = {}
        for next_node in neighbors:
            pheromone = self.G.edges[current_node, next_node]['pheromone'] ** self.alpha
            heuristic = self._get_heuristic_value(current_node, next_node) ** self.beta
            attractiveness[next_node] = pheromone * heuristic

        # Decide between exploitation (choosing the best option) and exploration (probabilistic choice)
        if random.random() < self.q0:
            return max(attractiveness, key=attractiveness.get) # Exploitation
        else:
            # Exploration
            total_attractiveness = sum(attractiveness.values())
            if total_attractiveness == 0:
                return random.choice(neighbors) # Failsafe for zero attractiveness
            
            probabilities = [val / total_attractiveness for val in attractiveness.values()]
            return random.choices(list(attractiveness.keys()), weights=probabilities, k=1)[0]

    def _run_single_ant(self):
        """Simulates the journey of a single ant from the start to the end node."""
        path = [self.start]
        visited = {self.start}
        current = self.start
        cost = 0

        while current != self.end:
            next_node = self._select_next_node(current, visited)
            if next_node is None:
                return None, float('inf') # Ant is stuck

            cost += self._get_dynamic_cost(current, next_node)
            path.append(next_node)
            visited.add(next_node)
            current = next_node

        return path, cost

    def _update_pheromones(self, ant_paths):
        """Updates pheromone levels based on evaporation and ant deposits."""
        # Evaporation: reduce pheromone on all edges
        for u, v in self.G.edges():
            self.G.edges[u, v]['pheromone'] *= (1 - self.rho)

        # Deposit: ants add pheromone to the paths they traveled
        for path, cost in ant_paths:
            if path is not None and cost != float('inf'):
                pheromone_deposit = self.Q / cost
                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    self.G.edges[u, v]['pheromone'] += pheromone_deposit

        # Elitism: add extra pheromone to the best path found so far
        if self.best_path:
            elitist_deposit = (self.Q * self.elitist_weight) / self.best_cost
            for i in range(len(self.best_path) - 1):
                u, v = self.best_path[i], self.best_path[i + 1]
                self.G.edges[u, v]['pheromone'] += elitist_deposit

    def solve(self):
        """The main loop of the ACO algorithm."""
        plot_checkpoints = {1, self.max_iterations // 2, self.max_iterations}

        print(f"Running ACO for {self.max_iterations} iterations...")
        for it in range(1, self.max_iterations + 1):
            ant_paths = [self._run_single_ant() for _ in range(self.num_ants)]

            # Capture a sample path for visualization at specific iterations
            if it in plot_checkpoints and ant_paths:
                self.sample_paths_for_plot[it] = ant_paths[0]

            # Update the best path found so far across all ants and iterations
            for path, cost in ant_paths:
                if path and cost < self.best_cost:
                    self.best_path, self.best_cost = path, cost
            
            self._update_pheromones(ant_paths)
            self.cost_history.append(self.best_cost)
            
            # Simulate traffic increase on the current best path, making it less desirable
            if self.best_path:
                for i in range(len(self.best_path) - 1):
                    u, v = self.best_path[i], self.best_path[i + 1]
                    self.G.edges[u, v]['current_traffic'] += 1
            
            if it % 10 == 0 or it == 1: # Print progress periodically
                 print(f"  Iteration {it}/{self.max_iterations} - Current Best Cost: {self.best_cost:.2f}")

        return self.best_path, self.best_cost, self.cost_history, self.sample_paths_for_plot


# --- 3. Visualization Functions ---

def plot_convergence_history(history):
    """Plots the convergence of the best path cost over iterations."""
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(12, 6))
    plt.plot(history, color='royalblue', linewidth=2)
    plt.title('ACO Cost Convergence Over Iterations', fontsize=16, fontweight='bold')
    plt.xlabel('Iteration', fontsize=12)
    plt.ylabel('Best Path Cost', fontsize=12)
    plt.tight_layout()
    plt.show()

def plot_network_path(graph, path, cost, title, start_node, end_node, layout, style_config):
    """Draws the network graph and highlights a specific path."""
    plt.figure(figsize=(12, 12))
    
    nx.draw(graph, layout, with_labels=True, **style_config['BASE_STYLE'])

    if path:
        path_edges = list(zip(path, path[1:]))
        nx.draw_networkx_edges(graph, layout, edgelist=path_edges, **style_config['PATH_STYLE'])
    
    nx.draw_networkx_nodes(graph, layout, nodelist=[start_node], **style_config['START_NODE_STYLE'])
    nx.draw_networkx_nodes(graph, layout, nodelist=[end_node], **style_config['END_NODE_STYLE'])

    plt.title(f"{title}\nCost: {cost:.2f}", fontsize=18, fontweight='bold')
    plt.show()

def plot_path_evolution(graph, sample_paths, start_node, end_node, layout, style_config):
    """Plots the path of a single ant at different stages of the simulation."""
    num_plots = len(sample_paths)
    if num_plots == 0: return
        
    fig, axes = plt.subplots(1, num_plots, figsize=(8 * num_plots, 8), constrained_layout=True)
    fig.suptitle("Evolution of a Sample Ant's Path", fontsize=22, fontweight='bold')
    
    axes = [axes] if num_plots == 1 else axes

    for ax, (it, (path, cost)) in zip(axes, sorted(sample_paths.items())):
        nx.draw(graph, layout, ax=ax, with_labels=True, **style_config['BASE_STYLE'])
        
        if path:
            path_edges = list(zip(path, path[1:]))
            nx.draw_networkx_edges(graph, layout, ax=ax, edgelist=path_edges, **style_config['EVOLUTION_PATH_STYLE'])

        nx.draw_networkx_nodes(graph, layout, ax=ax, nodelist=[start_node], **style_config['START_NODE_STYLE'])
        nx.draw_networkx_nodes(graph, layout, ax=ax, nodelist=[end_node], **style_config['END_NODE_STYLE'])
        
        ax.set_title(f"Iteration: {it}\nPath Cost: {cost:.2f}", fontsize=16)

    plt.show()


# --- 4. Main Execution ---
if __name__ == "__main__":
    # --- Configuration ---
    NETWORK_PARAMS = {'NUM_NODES': 15}
    START_NODE, END_NODE = 0, NETWORK_PARAMS['NUM_NODES'] - 1
    
    ACO_PARAMS = {
        'num_ants': 20,
        'num_iterations': 100,
        'alpha': 1.0,  # Pheromone importance
        'beta': 5.0,   # Heuristic importance
        'rho': 0.5,    # Evaporation rate
        'Q': 100,      # Pheromone deposit factor
        'q0': 0.9,     # Exploitation factor (high value = less exploration)
        'elitist_weight': 2.0
    }
    
    VISUAL_STYLE = {
        'BASE_STYLE': {
            'node_size': 500, 'node_color': 'skyblue', 'edge_color': 'lightgray',
            'width': 1.0, 'font_size': 10, 'arrows': True
        },
        'PATH_STYLE': {
            'edge_color': 'dodgerblue', 'width': 2.5, 'arrows': True, 'arrowsize': 20
        },
        'EVOLUTION_PATH_STYLE': {
            'edge_color': 'crimson', 'width': 2.5, 'arrows': True, 'arrowsize': 20
        },
        'DIJKSTRA_PATH_STYLE': {
            'edge_color': 'darkorange', 'width': 2.5, 'arrows': True, 'arrowsize': 20
        },
        'START_NODE_STYLE': {'node_color': 'limegreen', 'node_size': 700},
        'END_NODE_STYLE': {'node_color': 'tomato', 'node_size': 700}
    }

    # --- 1. Generate Network ---
    print("Generating traffic network...")
    network = generate_traffic_network(num_nodes=NETWORK_PARAMS['NUM_NODES'])
    fixed_layout = nx.spring_layout(network, seed=42) # Use a fixed layout for all plots
    
    # --- 2. Run Ant Colony Optimization ---
    print("\n--- Starting ACO Simulation ---")
    aco_solver = AntColonyOptimization(
        graph=network, start_node=START_NODE, end_node=END_NODE, **ACO_PARAMS
    )
    best_path_aco, best_cost_aco, history, sample_paths = aco_solver.solve()
    
    print("\n--- ACO Simulation Finished ---")
    print(f"Best Path Found by ACO: {best_path_aco}")
    print(f"Final Dynamic Cost: {best_cost_aco:.2f}")

    # --- 3. Visualize ACO Results ---
    plot_convergence_history(history)
    plot_path_evolution(network, sample_paths, START_NODE, END_NODE, fixed_layout, VISUAL_STYLE)
    
    aco_plot_style = VISUAL_STYLE.copy()
    plot_network_path(
        network, best_path_aco, best_cost_aco,
        'Optimal Path Found by ACO (Dynamic Cost)',
        START_NODE, END_NODE, fixed_layout, aco_plot_style
    )

    # --- 4. Compare with Dijkstra's Algorithm (Static Weights) ---
    print("\n--- Comparing with Dijkstra's Algorithm (Static Costs) ---")
    try:
        path_dijkstra = nx.shortest_path(network, source=START_NODE, target=END_NODE, weight="weight")
        cost_dijkstra = nx.path_weight(network, path_dijkstra, weight="weight")
        
        print(f"Shortest Path by Dijkstra: {path_dijkstra}")
        print(f"Static Cost: {cost_dijkstra:.2f}")

        dijkstra_plot_style = VISUAL_STYLE.copy()
        dijkstra_plot_style['PATH_STYLE'] = dijkstra_plot_style['DIJKSTRA_PATH_STYLE']
        plot_network_path(
            network, path_dijkstra, cost_dijkstra,
            "Shortest Path by Dijkstra (Static Cost)",
            START_NODE, END_NODE, fixed_layout, dijkstra_plot_style
        )
    except nx.NetworkXNoPath:
        print(f"No path exists between {START_NODE} and {END_NODE} for Dijkstra's algorithm.")