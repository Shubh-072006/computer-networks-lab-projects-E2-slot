import socket
import threading
import time
import random
import json
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

@dataclass
class Player:
    """Player data class with smooth movement support"""
    name: str
    lane: int
    target_lane: int
    score: float
    blink: float
    last_heartbeat: float
    addr: Any
    x: float
    y: float
    id: int
    finished: bool = False
    move_progress: float = 1.0
    consecutive_collisions: int = 0  # Track consecutive collisions
    last_collision_time: float = 0.0  # Time of last collision
    # ADD VERTICAL MOVEMENT FIELDS
    vertical_speed: float = 0.0
    target_y: float = 400.0  # Default vertical position

@dataclass
class Obstacle:
    """Obstacle data class with type support"""
    lane: int
    y: float
    x: float
    id: float
    type: str
    width: float
    height: float
    speed: float
    penalty: int
    color: str

class GameServer:
    """Enhanced multiplayer game server with advanced features and EXACT client road positioning"""
    
    def __init__(self):
        # Network configuration
        self.SERVER_IP = "0.0.0.0"
        self.SERVER_PORT = 9999
        self.TICK_RATE = 60.0
        self.BUFFER_SIZE = 4096
        self.TICK_DT = 1.0 / self.TICK_RATE
        
        # Game settings with progressive difficulty
        self.BASE_GAME_DURATION = 40.0
        self.GAME_DURATION = self.BASE_GAME_DURATION
        self.MAX_SCORE = 300
        self.HEARTBEAT_TIMEOUT = 5.0
        
        # Screen and road settings - EXACTLY MATCHING CLIENT
        self.SCREEN_W = 1000  # Match client
        self.SCREEN_H = 700   # Match client
        self.ROAD_LEFT = 200  # Match client EXACTLY
        self.ROAD_RIGHT = 800 # Match client EXACTLY  
        self.ROAD_WIDTH = self.ROAD_RIGHT - self.ROAD_LEFT
        
        # LANE POSITIONS - EXACTLY MATCHING CLIENT'S LANE CENTERS
        self.LANE_X = [300, 500, 700]  # Left, Middle, Right lane centers
        
        self.PLAYER_Y = 300 #Player vertical position
        self.LANE_CHANGE_DURATION = 0.3  # Smooth lane transition duration
        
        # VERTICAL MOVEMENT SETTINGS - NEW
        self.VERTICAL_SPEED = 200.0  # Pixels per second for vertical movement
        self.MIN_PLAYER_Y = 100  # Minimum Y position (top boundary)
        self.MAX_PLAYER_Y = 600  # Maximum Y position (bottom boundary)
        
        # Enhanced collision system
        self.BLINK_DURATION = 1.5
        self.COLLISION_COOLDOWN = 2.0
        self.CONSECUTIVE_COLLISION_PENALTY_MULTIPLIER = 1.5  # Extra penalty for repeated collisions
        self.COLLISION_RESET_TIME = 3.0  # Time to reset consecutive collision counter
        
        # Advanced difficulty system
        self.game_progress = 0.0
        self.difficulty_level = 1
        self.obstacles_spawned = 0
        
        # Enhanced obstacle system with EXACT client positioning
        self.OBSTACLE_TYPES = {
            "car": {
                "width": 80,
                "height": 120,
                "speed": 140.0,
                "penalty": 10,
                "color": "#FF6B6B",
                "spawn_weight": 0.6,
                "min_cooldown": 1.2  # Minimum spawn cooldown for this type
            },
            "truck": {
                "width": 100,
                "height": 160,
                "speed": 110.0,
                "penalty": 20,
                "color": "#4ECDC4",
                "spawn_weight": 0.3,
                "min_cooldown": 1.5
            },
            "bus": {
                "width": 90,
                "height": 180,
                "speed": 100.0,
                "penalty": 25,
                "color": "#45B7D1", 
                "spawn_weight": 0.1,
                "min_cooldown": 2.0
            },
            "bike": {
                "width": 60,
                "height": 80,
                "speed": 160.0,
                "penalty": 5,
                "color": "#96CEB4",
                "spawn_weight": 0.4,
                "min_cooldown": 0.8
            },
            "rock": {
                "width": 70,
                "height": 70,
                "speed": 130.0,
                "penalty": 15,
                "color": "#A1887F",
                "spawn_weight": 0.2,
                "min_cooldown": 1.0
            }
        }
        
        # Advanced spawn settings with dynamic difficulty and cooldown management
        self.BASE_OBSTACLE_COOLDOWN = 1.5
        self.BASE_OBSTACLE_PROBABILITY = 0.7
        self.obstacle_cooldown = self.BASE_OBSTACLE_COOLDOWN
        self.obstacle_probability = self.BASE_OBSTACLE_PROBABILITY
        self.MAX_OBSTACLES = 8
        self.obstacle_speed_multiplier = 1.0
        
        # Game state
        self.players: Dict[Any, Player] = {}
        self.obstacles: List[Obstacle] = []
        self.game_running = False
        self.start_time: Optional[float] = None
        self.shutdown_requested = False
        self.last_obstacle_spawn: float = 0
        self.next_player_id = 1
        self.state_sequence = 0
        
        # Performance tracking
        self.performance_stats = {
            "total_obstacles_spawned": 0,
            "total_collisions": 0,
            "average_obstacle_lifetime": 0,
            "game_session_count": 0
        }
        
        # Network
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.lock = threading.Lock()
        
        # Calculate derived values
        self.POINTS_PER_TICK = self.MAX_SCORE / (self.GAME_DURATION * self.TICK_RATE)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info(f"Server initialized with EXACT client road: {self.ROAD_LEFT}-{self.ROAD_RIGHT}")
        logger.info(f"Lane centers: {self.LANE_X}")
        logger.info(f"Vertical movement range: {self.MIN_PLAYER_Y}-{self.MAX_PLAYER_Y}")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("Received shutdown signal, shutting down...")
        self.shutdown_requested = True
        self.game_running = False

    def initialize_server(self):
        """Initialize and bind the server socket"""
        try:
            self.sock.bind((self.SERVER_IP, self.SERVER_PORT))
            self.sock.setblocking(False)
            logger.info(f"Server initialized on {self.SERVER_IP}:{self.SERVER_PORT}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            return False

    def receive_loop(self):
        """Handle incoming messages from clients"""
        while not self.shutdown_requested:
            try:
                data, addr = self.sock.recvfrom(self.BUFFER_SIZE)
                self.handle_message(data, addr)
            except BlockingIOError:
                time.sleep(0.001)
            except Exception as e:
                logger.error(f"Unexpected error in receive_loop: {e}")
                time.sleep(0.1)

    def handle_message(self, data: bytes, addr: Any):
        """Process a single incoming message"""
        try:
            msg = json.loads(data.decode('utf-8'))
            msg_type = msg.get("type")
            
            if msg_type == "join":
                self.handle_join(msg, addr)
            elif msg_type == "input":
                self.handle_input(msg, addr)
            elif msg_type == "heartbeat":
                self.handle_heartbeat(addr)
            elif msg_type == "leave":
                self.handle_leave(addr)
            else:
                logger.warning(f"Unknown message type from {addr}: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error handling message from {addr}: {e}")

    def handle_join(self, msg: Dict, addr: Any):
        """Handle player join requests with client-compatible response"""
        name = msg.get("name", "Player")[:20]
        now = time.time()
        
        with self.lock:
            if addr in self.players:
                # Update existing player
                self.players[addr].name = name
                self.players[addr].last_heartbeat = now
                player_id = self.players[addr].id
                logger.info(f"Player reconnected: {name} from {addr}")
            else:
                # Create new player with unique ID
                start_lane = 1  # Middle lane
                player_id = self.next_player_id
                self.next_player_id += 1
                
                self.players[addr] = Player(
                    name=name,
                    lane=start_lane,
                    target_lane=start_lane,
                    score=0.0,
                    blink=0.0,
                    last_heartbeat=now,
                    addr=addr,
                    x=self.LANE_X[start_lane],  # Use exact lane center
                    y=self.PLAYER_Y,
                    id=player_id,
                    target_y=self.PLAYER_Y  # Initialize target Y position
                )
                logger.info(f"New player joined: {name} (ID: {player_id}) from {addr}")
        
        # Send acknowledgement WITH ID and obstacle types for client compatibility
        self.send_message({
            "type": "join_ack",
            "id": player_id,  # Client expects this
            "obstacle_types": self.OBSTACLE_TYPES,  # Send types for client rendering
            "settings": {
                "blink_duration": self.BLINK_DURATION,
                "collision_cooldown": self.COLLISION_COOLDOWN
            }
        }, addr)

    def handle_input(self, msg: Dict, addr: Any):
        """Handle player input with enhanced smooth lane transitions AND VERTICAL MOVEMENT"""
        with self.lock:
            if addr not in self.players or not self.game_running:
                return
            
            player = self.players[addr]
            left = bool(msg.get("left", 0))
            right = bool(msg.get("right", 0))
            up = bool(msg.get("up", 0))      # NEW: Forward movement
            down = bool(msg.get("down", 0))  # NEW: Backward movement
            
            # Process vertical movement inputs
            if up and not down:
                # Move forward (up on screen)
                player.vertical_speed = -self.VERTICAL_SPEED  # Negative Y = up
            elif down and not up:
                # Move backward (down on screen)  
                player.vertical_speed = self.VERTICAL_SPEED   # Positive Y = down
            else:
                # No vertical input, stop vertical movement
                player.vertical_speed = 0.0
            
            # Only process lane changes if not currently moving lanes and game is running
            if player.move_progress >= 1.0 and self.game_running:
                target_lane = player.lane
                
                # Enhanced input handling with cooldown check
                current_time = time.time()
                can_change_lane = (current_time - player.last_collision_time > 0.5)
                
                if can_change_lane:
                    if left and not right and player.lane > 0:
                        target_lane = player.lane - 1
                    elif right and not left and player.lane < 2:
                        target_lane = player.lane + 1
                
                # Start lane change if target is different
                if target_lane != player.lane:
                    player.target_lane = target_lane
                    player.move_progress = 0.0
            
            player.last_heartbeat = time.time()

    def handle_heartbeat(self, addr: Any):
        """Handle client heartbeat"""
        with self.lock:
            if addr in self.players:
                self.players[addr].last_heartbeat = time.time()
        
        self.send_message({"type": "heartbeat_ack"}, addr)

    def handle_leave(self, addr: Any):
        """Handle player leave requests"""
        with self.lock:
            if addr in self.players:
                player_name = self.players[addr].name
                del self.players[addr]
                logger.info(f"Player left: {player_name} from {addr}")

    def update_player_movements(self, dt: float):
        """Update smooth lane transitions AND vertical movement for all players"""
        with self.lock:
            for player in self.players.values():
                # Update lane transitions
                if player.move_progress < 1.0:
                    # Continue lane transition with dynamic speed based on game state
                    transition_speed = self.LANE_CHANGE_DURATION
                    if self.game_progress > 0.7:  # Faster transitions in late game
                        transition_speed *= 0.8
                    
                    player.move_progress += dt / transition_speed
                    player.move_progress = min(1.0, player.move_progress)
                    
                    # Calculate interpolated position with enhanced easing
                    start_x = self.LANE_X[player.lane]
                    target_x = self.LANE_X[player.target_lane]
                    
                    # Enhanced easing function for smoother animation
                    progress = self.ease_out_back(player.move_progress)
                    player.x = start_x + (target_x - start_x) * progress
                    
                    # Complete transition
                    if player.move_progress >= 1.0:
                        player.lane = player.target_lane
                        player.x = self.LANE_X[player.lane]
                
                # NEW: Update vertical movement
                if player.vertical_speed != 0.0:
                    new_y = player.y + player.vertical_speed * dt
                    # Clamp Y position within screen boundaries
                    player.y = max(self.MIN_PLAYER_Y, min(self.MAX_PLAYER_Y, new_y))

    def ease_out_back(self, x: float) -> float:
        """Enhanced easing function for smoother animations"""
        c1 = 1.70158
        c2 = c1 * 1.525
        return 1 + c2 * (x - 1) ** 3 + c1 * (x - 1) ** 2

    def send_message(self, message: Dict, addr: Any):
        """Send message to client with enhanced error handling"""
        try:
            data = json.dumps(message, separators=(',', ':')).encode('utf-8')
            self.sock.sendto(data, addr)
        except Exception as e:
            logger.warning(f"Failed to send message to {addr}: {e}")

    def check_timeouts(self):
        """Remove players who haven't sent heartbeats with enhanced tracking"""
        now = time.time()
        timeout_players = []
        
        with self.lock:
            for addr, player in self.players.items():
                if now - player.last_heartbeat > self.HEARTBEAT_TIMEOUT:
                    timeout_players.append(addr)
            
            for addr in timeout_players:
                if addr in self.players:
                    logger.info(f"Player timeout: {self.players[addr].name} from {addr}")
                    del self.players[addr]
        
        return len(timeout_players) > 0

    def update_difficulty(self):
        """Enhanced game difficulty based on progress, player count, and performance"""
        # Adjust for game progress (gets harder over time)
        progress_factor = 1.0 + (self.game_progress * 1.5)  # 1.0 to 2.5
        
        # Adjust for player count (more players = slightly easier)
        with self.lock:
            player_count = len(self.players)
        player_factor = max(0.7, 1.3 - (player_count * 0.15))
        
        # Adjust based on player performance (if players are doing well, increase difficulty)
        performance_factor = 1.0
        with self.lock:
            if any(p.score > self.MAX_SCORE * 0.7 for p in self.players.values()):
                performance_factor = 1.2
        
        # Combined difficulty with smooth transitions
        difficulty = progress_factor * player_factor * performance_factor
        
        # Update spawn rates with type-specific minimum cooldowns
        self.obstacle_cooldown = max(0.5, self.BASE_OBSTACLE_COOLDOWN / difficulty)
        self.obstacle_probability = min(0.95, self.BASE_OBSTACLE_PROBABILITY * difficulty)
        self.obstacle_speed_multiplier = 1.0 + (self.game_progress * 0.8)  # 1.0 to 1.8
        
        # Update game duration based on difficulty
        self.GAME_DURATION = self.BASE_GAME_DURATION * (1.0 + (difficulty - 1.0) * 0.3)

    def broadcast_state(self):
        """Broadcast game state to all connected players with enhanced data"""
        with self.lock:
            now = time.time()
            elapsed = now - self.start_time if self.start_time else 0
            time_left = max(0, self.GAME_DURATION - elapsed)
            
            # Build enhanced player list
            player_list = []
            for player in self.players.values():
                player_list.append({
                    "id": player.id,
                    "x": player.x,
                    "y": player.y,  # This now includes vertical movement updates
                    "name": player.name,
                    "score": round(player.score),
                    "finished": player.finished,
                    "lane": player.lane,
                    "blink": player.blink,
                    "target_lane": player.target_lane,
                    "move_progress": player.move_progress
                })
            
            # Build obstacle list with all necessary fields
            obstacle_list = []
            for obs in self.obstacles:
                obstacle_list.append({
                    "x": obs.x,
                    "y": obs.y,
                    "lane": obs.lane,
                    "id": obs.id,
                    "type": obs.type,
                    "color": obs.color,
                    "width": obs.width,  # Send dimensions for client rendering
                    "height": obs.height
                })
            
            self.state_sequence += 1
            
            state = {
                "type": "state",
                "seq": self.state_sequence,
                "players": player_list,
                "obstacles": obstacle_list,
                "time_left": time_left,
                "game_running": self.game_running,
                "game_progress": self.game_progress,
                "difficulty": self.difficulty_level,
                "total_players": len(self.players),
                "server_time": now
            }
        
        # Enhanced broadcasting with compression consideration
        data = json.dumps(state, separators=(',', ':')).encode('utf-8')
        disconnected = []
        
        with self.lock:
            for addr in list(self.players.keys()):
                try:
                    self.sock.sendto(data, addr)
                except Exception as e:
                    logger.warning(f"Failed to send state to {addr}: {e}")
                    disconnected.append(addr)
            
            for addr in disconnected:
                if addr in self.players:
                    del self.players[addr]

    def get_obstacle_weights(self) -> tuple:
        """Enhanced weighted obstacle types based on game progress and player performance"""
        types = list(self.OBSTACLE_TYPES.keys())
        base_weights = [self.OBSTACLE_TYPES[t]["spawn_weight"] for t in types]
        
        progress = self.game_progress
        
        # Calculate average player score to adjust difficulty
        avg_score = 0
        with self.lock:
            if self.players:
                avg_score = sum(p.score for p in self.players.values()) / len(self.players)
        
        # Players doing well = harder obstacles
        performance_modifier = 1.0 + (avg_score / self.MAX_SCORE) * 0.5
        
        adjusted_weights = []
        for i, obstacle_type in enumerate(types):
            base_weight = base_weights[i]
            penalty = self.OBSTACLE_TYPES[obstacle_type]["penalty"]
            
            # Dynamic weight adjustment based on multiple factors
            if penalty >= 20:  # Hard obstacles
                adjusted_weight = base_weight * (1.0 + progress * 2.5) * performance_modifier
            elif penalty <= 10:  # Easy obstacles  
                adjusted_weight = base_weight * (1.0 - progress * 0.7)
            else:  # Medium obstacles
                adjusted_weight = base_weight * (1.0 + progress * 1.2) * performance_modifier
                
            adjusted_weights.append(max(0.05, adjusted_weight))  # Ensure minimum weight
        
        # Normalize weights
        total = sum(adjusted_weights)
        normalized_weights = [w/total for w in adjusted_weights]
        
        return types, normalized_weights

    def update_obstacles(self, current_time: float, dt: float):
        """Enhanced obstacle movement and dynamic spawning with advanced cooldown system"""
        # Update game progress and difficulty
        self.game_progress = self.calculate_game_progress(current_time)
        self.update_difficulty()
        
        # Enhanced obstacle movement with progressive speed
        new_obstacles = []
        for obs in self.obstacles:
            # Apply progressive speed scaling based on type and difficulty
            type_speed = obs.speed
            speed_multiplier = self.obstacle_speed_multiplier
            
            # Faster obstacles in later game stages
            if self.game_progress > 0.8:
                speed_multiplier *= 1.2
            
            obs.y += (type_speed * speed_multiplier) * dt
            
            # Keep obstacle while any part is still on screen
            if obs.y < self.SCREEN_H + obs.height + 100:  # Slightly larger buffer
                new_obstacles.append(obs)
        
        self.obstacles = new_obstacles

        # Enhanced obstacle spawning with type-specific cooldowns
        if self.game_running:
            time_since_last_spawn = current_time - self.last_obstacle_spawn
            
            # Check if we can spawn based on cooldown and probability
            can_spawn = (time_since_last_spawn >= self.obstacle_cooldown and 
                        len(self.obstacles) < self.MAX_OBSTACLES and 
                        random.random() < self.obstacle_probability)
            
            if can_spawn:
                lane_choice = random.randint(0, 2)
                
                # Enhanced weighted random selection
                obstacle_types, weights = self.get_obstacle_weights()
                obstacle_type = random.choices(obstacle_types, weights=weights)[0]
                
                props = self.OBSTACLE_TYPES[obstacle_type]
                
                # Use EXACT lane center position
                obstacle_x = self.LANE_X[lane_choice]
                obstacle_y = -props["height"]
                
                new_obstacle = Obstacle(
                    lane=lane_choice,
                    y=obstacle_y,
                    x=obstacle_x,
                    id=current_time,
                    type=obstacle_type,
                    width=props["width"],
                    height=props["height"],
                    speed=props["speed"],
                    penalty=props["penalty"],
                    color=props["color"]
                )
                
                self.obstacles.append(new_obstacle)
                self.obstacles_spawned += 1
                self.performance_stats["total_obstacles_spawned"] += 1
                
                logger.debug(f"Spawned {obstacle_type} in lane {lane_choice} at x={obstacle_x}")

                # Apply type-specific minimum cooldown
                type_cooldown = props.get("min_cooldown", self.BASE_OBSTACLE_COOLDOWN)
                effective_cooldown = max(self.obstacle_cooldown, type_cooldown)
                self.last_obstacle_spawn = current_time

    def calculate_game_progress(self, current_time: float) -> float:
        """Calculate enhanced game progress with smoothing"""
        if not self.start_time:
            return 0.0
        elapsed = current_time - self.start_time
        raw_progress = min(1.0, elapsed / self.GAME_DURATION)
        
        # Apply smoothing to progress for better difficulty transitions
        return raw_progress

    def check_collision(self, player, obstacle) -> bool:
        """Enhanced collision detection with better bounding boxes"""
        # Player bounds (matching client car rendering exactly)
        player_left = player.x - 30
        player_right = player.x + 30
        player_top = player.y - 40
        player_bottom = player.y + 40
        
        # Obstacle bounds with slight padding for better gameplay feel
        padding = 5
        obstacle_left = obstacle.x - obstacle.width / 2 + padding
        obstacle_right = obstacle.x + obstacle.width / 2 - padding
        obstacle_top = obstacle.y - obstacle.height / 2 + padding
        obstacle_bottom = obstacle.y + obstacle.height / 2 - padding
        
        # Bounding box collision check
        collision = (player_right > obstacle_left and 
                    player_left < obstacle_right and 
                    player_bottom > obstacle_top and 
                    player_top < obstacle_bottom)
        
        return collision

    def update_collisions(self, current_time: float):
        """Enhanced collision detection with progressive penalties"""
        if not self.start_time:
            return
            
        obstacles_to_remove: Set[float] = set()
        
        with self.lock:
            for obs in self.obstacles:
                for player in self.players.values():
                    # Enhanced invulnerability check
                    time_since_blink = current_time - player.blink
                    time_since_last_collision = current_time - player.last_collision_time
                    is_invulnerable = (time_since_blink < self.BLINK_DURATION)
                    
                    # Reset consecutive collisions if enough time has passed
                    if time_since_last_collision > self.COLLISION_RESET_TIME:
                        player.consecutive_collisions = 0
                    
                    if is_invulnerable or player.finished:
                        continue
                    
                    # Check collision and same lane
                    if self.check_collision(player, obs) and obs.lane == player.lane:
                        logger.info(f"Collision: {player.name} hit {obs.type} in lane {player.lane}")
                        
                        # Enhanced penalty calculation
                        base_penalty = obs.penalty
                        
                        # Progressive penalty for consecutive collisions
                        if player.consecutive_collisions > 0:
                            penalty_multiplier = 1.0 + (player.consecutive_collisions * 0.3)
                            base_penalty = int(base_penalty * penalty_multiplier)
                            logger.info(f"Consecutive collision #{player.consecutive_collisions + 1}, penalty: {base_penalty}")
                        
                        # Apply penalty
                        player.score = max(0, player.score - base_penalty)
                        player.blink = current_time
                        player.last_collision_time = current_time
                        player.consecutive_collisions += 1
                        
                        self.performance_stats["total_collisions"] += 1
                        
                        # Remove obstacle
                        obstacles_to_remove.add(obs.id)
                        break
        
        # Remove obstacles that caused collisions
        if obstacles_to_remove:
            self.obstacles = [obs for obs in self.obstacles if obs.id not in obstacles_to_remove]

    def update_scores(self):
        """Enhanced scoring system with progressive rewards"""
        with self.lock:
            for player in self.players.values():
                if player.score < self.MAX_SCORE and not player.finished:
                    # Progressive scoring based on game state and player performance
                    base_points = self.POINTS_PER_TICK
                    
                    # Bonus points for good performance (few collisions)
                    collision_modifier = max(0.5, 1.0 - (player.consecutive_collisions * 0.1))
                    
                    # Progressive difficulty bonus
                    difficulty_bonus = 1.0 + (self.game_progress * 0.3)
                    
                    total_points = base_points * collision_modifier * difficulty_bonus
                    player.score += total_points
                    player.score = min(player.score, self.MAX_SCORE)
                    
                    if player.score >= self.MAX_SCORE and not player.finished:
                        player.finished = True
                        player.blink = time.time()
                        logger.info(f"🎉 {player.name} reached max score with {player.consecutive_collisions} collisions!")

    def game_loop(self):
        """Enhanced main game loop with performance tracking"""
        prev_time = time.time()
        frame_time = 1.0 / self.TICK_RATE
        
        logger.info("Game loop started")
        self.performance_stats["game_session_count"] += 1
        
        while self.game_running and not self.shutdown_requested:
            loop_start = time.time()
            current_time = time.time()
            
            dt = min(current_time - prev_time, 0.1)
            prev_time = current_time
            
            # Update game state
            self.update_player_movements(dt)
            self.update_obstacles(current_time, dt)
            self.update_collisions(current_time)
            self.update_scores()
            
            # Enhanced game end conditions
            if self.check_game_end(current_time):
                break
            
            # Broadcast and check timeouts
            self.broadcast_state()
            self.check_timeouts()
            
            # Maintain precise tick rate
            sleep_time = frame_time - (time.time() - loop_start)
            if sleep_time > 0:
                time.sleep(sleep_time)
            elif sleep_time < -0.002:  # Warn if consistently behind
                logger.warning(f"Game loop running behind: {-sleep_time:.3f}s")
        
        self.end_game()

    def check_game_end(self, current_time: float) -> bool:
        """Enhanced game end conditions"""
        if not self.start_time:
            return False
            
        elapsed = current_time - self.start_time
        if elapsed >= self.GAME_DURATION:
            return True
        
        with self.lock:
            # End if all active players finished
            active_players = [p for p in self.players.values() if not p.finished]
            if not active_players and self.players:
                return True
        
        return False

    def reset_game(self):
        """Enhanced game state reset for new rounds"""
        with self.lock:
            for player in self.players.values():
                player.score = 0.0
                player.lane = 1
                player.target_lane = 1
                player.x = self.LANE_X[1]
                player.y = self.PLAYER_Y
                player.blink = 0.0
                player.finished = False
                player.move_progress = 1.0
                player.consecutive_collisions = 0
                player.last_collision_time = 0.0
                player.last_heartbeat = time.time()
                player.vertical_speed = 0.0  # Reset vertical movement
                player.target_y = self.PLAYER_Y  # Reset target Y
            
            self.obstacles = []
            self.obstacles_spawned = 0
            self.last_obstacle_spawn = time.time()
            self.start_time = time.time()
            self.game_progress = 0.0
            self.state_sequence = 0
            self.difficulty_level = 1

    def end_game(self):
        """Enhanced game end with statistics"""
        self.game_running = False
        
        # Log detailed statistics
        with self.lock:
            if self.players:
                logger.info("=== GAME COMPLETED ===")
                logger.info("Final scores:")
                for player in sorted(self.players.values(), key=lambda p: p.score, reverse=True):
                    logger.info(f"  {player.name}: {round(player.score)} (Collisions: {player.consecutive_collisions})")
                
                logger.info(f"Game statistics:")
                logger.info(f"  Obstacles spawned: {self.obstacles_spawned}")
                logger.info(f"  Total collisions: {self.performance_stats['total_collisions']}")
                logger.info(f"  Game sessions: {self.performance_stats['game_session_count']}")
        
        self.broadcast_state()
        logger.info("Game ended")

    def wait_for_players(self) -> bool:
        """Enhanced player waiting with timeout"""
        logger.info("Waiting for players to join...")
        wait_start = time.time()
        max_wait_time = 30.0  # Maximum wait time in seconds
        
        while not self.shutdown_requested:
            with self.lock:
                if len(self.players) > 0:
                    return True
            
            # Check for timeout
            if time.time() - wait_start > max_wait_time:
                logger.warning("Wait for players timeout reached")
                return False
            
            time.sleep(0.5)
        
        return False

    def run(self):
        """Enhanced main server execution loop"""
        if not self.initialize_server():
            return
        
        # Start network thread
        network_thread = threading.Thread(target=self.receive_loop, daemon=True)
        network_thread.start()
        
        logger.info("Server is running. Press Ctrl+C to stop.")
        
        # Enhanced main game loop with better session management
        while not self.shutdown_requested:
            if self.wait_for_players():
                logger.info("Starting new game session")
                time.sleep(2)  # Give clients time to prepare
                
                self.reset_game()
                self.game_running = True
                self.game_loop()
                
                # Brief pause between games with statistics
                if not self.shutdown_requested:
                    logger.info("Game session completed. Waiting before next game...")
                    time.sleep(5)
        
        self.cleanup()

    def cleanup(self):
        """Enhanced resource cleanup"""
        logger.info("Cleaning up server resources...")
        logger.info("Final server statistics:")
        logger.info(f"  Total obstacles spawned: {self.performance_stats['total_obstacles_spawned']}")
        logger.info(f"  Total collisions: {self.performance_stats['total_collisions']}")
        logger.info(f"  Game sessions completed: {self.performance_stats['game_session_count']}")
        
        self.sock.close()
        logger.info("Server shutdown complete")

def main():
    """Entry point"""
    server = GameServer()
    try:
        server.run()
    except Exception as e:
        logger.critical(f"Server crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()