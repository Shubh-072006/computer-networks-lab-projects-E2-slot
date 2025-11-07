import socket, json, time, argparse, pygame

SERVER_PORT = 9999
HEARTBEAT_SEND_DT = 1.0  # Send a packet every 1 second minimum

SCREEN_W, SCREEN_H = 1000, 700
ROAD_LEFT, ROAD_RIGHT = 200, 800
ROAD_WIDTH = ROAD_RIGHT - ROAD_LEFT

parser = argparse.ArgumentParser()
parser.add_argument("server_ip")
parser.add_argument("--name", default="Player")
args = parser.parse_args()

server = (args.server_ip, SERVER_PORT)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(False)

# --- Reliable join setup ---
JOIN_RETRY = 0.8
JOIN_TIMEOUT = 8.0
join_sent_at = 0.0
join_deadline = time.time() + JOIN_TIMEOUT
player_id = None
join_confirmed = False

# Send initial join message (will be resent until ack)
def send_join():
    try:
        sock.sendto(json.dumps({"type": "join", "name": args.name}).encode(), server)
    except Exception as ex:
        print("Join send error:", ex)

send_join()
join_sent_at = time.time()

# --- CONSTANTS AND STATE VARIABLES ---
COLORS = [(255, 50, 50), (50, 200, 50), (50, 120, 255), (255, 200, 50)]

# Obstacle type definitions (should match server)
OBSTACLE_TYPES = {
    "car": {
        "width": 80,
        "height": 120,
        "color": "#FF6B6B"
    },
    "truck": {
        "width": 100,
        "height": 160,
        "color": "#4ECDC4"
    },
    "bus": {
        "width": 90,
        "height": 180,
        "color": "#45B7D1"
    },
    "bike": {
        "width": 60,
        "height": 80,
        "color": "#96CEB4"
    },
    "rock": {
        "width": 70,
        "height": 70,
        "color": "#A1887F"
    }
}

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

targets = {}
interp = {}
current_obstacles = []
player_scores = {}

last_send = 0.0

game_time_left = 0
game_running = False

# Input states
key_left_down = False
key_right_down = False
key_up_down = False    # Forward movement
key_down_down = False  # Backward movement

last_seq = -1  # sequence filtering for 'state' packets

# --- Pygame Initialization ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("LAN Racer - 3 Lane Mode with Vertical Movement")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)
bold_font = pygame.font.SysFont("Arial", 20, bold=True)
large_font = pygame.font.SysFont("Arial", 80, bold=True)# cache it
emoji_font = pygame.font.SysFont("Segoe UI Emoji", 80)
def draw_car(screen, x, y, color):
    # Body (shorter height: 60 instead of 80)
    pygame.draw.rect(screen, color, (x - 20, y - 30, 40, 60))

    # Windows (adjusted closer together)
    pygame.draw.rect(screen, (200, 200, 200), (x - 15, y - 25, 30, 15))
    pygame.draw.rect(screen, (200, 200, 200), (x - 15, y - 5, 30, 15))

    # Wheels (moved closer since car is shorter)
    pygame.draw.rect(screen, (0, 0, 0), (x - 25, y - 30, 10, 15))  # left top
    pygame.draw.rect(screen, (0, 0, 0), (x + 15, y - 30, 10, 15))  # right top
    pygame.draw.rect(screen, (0, 0, 0), (x - 25, y + 15, 10, 15))  # left bottom
    pygame.draw.rect(screen, (0, 0, 0), (x + 15, y + 15, 10, 15))  # right bottom

def draw_obstacle(screen, x, y, obs_type, color=None):
    """Draw obstacle based on type with proper dimensions and color"""
    # Get obstacle properties
    props = OBSTACLE_TYPES.get(obs_type, OBSTACLE_TYPES["car"])
    width = props["width"]
    height = props["height"]
    
    # Use provided color or default from type
    if color and color.startswith('#'):
        obstacle_color = hex_to_rgb(color)
    else:
        obstacle_color = hex_to_rgb(props["color"])
    
    # Draw the obstacle body
    pygame.draw.rect(screen, obstacle_color, (x - width/2, y - height/2, width, height))
    
    # Add details based on obstacle type
    if obs_type == "car":
        # Car windows
        window_color = (180, 180, 220)
        pygame.draw.rect(screen, window_color, (x - width/3, y - height/3, width*0.6, height/4))
    elif obs_type == "truck":
        # Truck cabin
        cabin_color = (100, 100, 150)
        pygame.draw.rect(screen, cabin_color, (x - width/2, y - height/2, width/2, height/2))
    elif obs_type == "bus":
        # Bus windows
        window_color = (180, 180, 220)
        for i in range(3):
            pygame.draw.rect(screen, window_color, 
                           (x - width/2 + 10 + i*25, y - height/3, 20, height/4))
    elif obs_type == "bike":
        # Bike handles and seat
        pygame.draw.rect(screen, (50, 50, 50), (x - width/2, y - height/4, width, 5))
        pygame.draw.circle(screen, (100, 100, 100), (int(x), int(y - height/4)), 8)
    elif obs_type == "rock":
        # Rocky texture
        for dx, dy in [(-10, -5), (5, -8), (0, 10), (8, 5)]:
            pygame.draw.circle(screen, (120, 100, 80), (int(x + dx), int(y + dy)), 5)

running = True
while running:
    now = time.time()

    # --- Retry join until ack (reliable join) ---
    if not join_confirmed:
        if now - join_sent_at >= JOIN_RETRY:
            send_join()
            join_sent_at = now
        if now > join_deadline:
            pass

    left = 0
    right = 0
    up = 0    # Forward movement
    down = 0  # Backward movement

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN and game_running:
            if event.key == pygame.K_LEFT and not key_left_down:
                left = 1
                key_left_down = True
            elif event.key == pygame.K_RIGHT and not key_right_down:
                right = 1
                key_right_down = True
            elif event.key == pygame.K_UP and not key_up_down:    # Forward
                up = 1
                key_up_down = True
            elif event.key == pygame.K_DOWN and not key_down_down:  # Backward
                down = 1
                key_down_down = True

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                key_left_down = False
            elif event.key == pygame.K_RIGHT:
                key_right_down = False
            elif event.key == pygame.K_UP:
                key_up_down = False
            elif event.key == pygame.K_DOWN:
                key_down_down = False

    # --- SEND LOGIC (Discrete Input & Heartbeat) ---
    send_input = (left or right or up or down)
    send_heartbeat = (now - last_send >= HEARTBEAT_SEND_DT)

    if send_input or send_heartbeat:
        msg = {"type": "input", "left": left, "right": right, "up": up, "down": down}
        try:
            sock.sendto(json.dumps(msg).encode(), server)
        except Exception as ex:
            print("Send error:", ex)
        last_send = now

    # --- RECEIVE LOGIC ---
    try:
        while True:
            try:
                data, addr = sock.recvfrom(8192)
            except BlockingIOError:
                break
            except Exception as ex:
                print("Recv error (inner):", ex)
                break

            try:
                p = json.loads(data.decode())
            except json.JSONDecodeError as ex:
                print("JSON decode error:", ex)
                continue
            except Exception as ex:
                print("Unexpected decode error:", ex)
                continue

            # Handle join_ack
            if p.get("type") == "join_ack":
                pid = p.get("id")
                if pid is not None:
                    player_id = pid
                    join_confirmed = True
                    print(f"Received join_ack: id={player_id}")
                    
                    # Update obstacle types if server sends them
                    if "obstacle_types" in p:
                        OBSTACLE_TYPES.update(p["obstacle_types"])
                        print("Updated obstacle types from server")
                        
            elif p.get("type") == "state":
                # sequence check
                seq = p.get("seq", None)
                if seq is not None:
                    if seq <= last_seq:
                        continue
                    last_seq = seq

                game_running = p.get("game_running", False)
                game_time_left = p.get("time_left", 0)

                # Update players
                for info in p.get("players", []):
                    pid = info["id"]
                    x = info["x"]
                    y = info["y"]  # Now includes vertical position from server
                    targets[pid] = {"x": x, "y": y, "name": info.get("name", f"Player{pid}")}
                    if pid not in interp:
                        interp[pid] = {"x": x, "y": y}
                    player_scores[pid] = {
                        "name": info.get("name", f"Player{pid}"),
                        "score": info.get("score", 0),
                        "finished": info.get("finished", False)
                    }

                # Update obstacles with server data
                current_obstacles = []
                for obs in p.get("obstacles", []):
                    # Ensure obstacle has all required fields with defaults
                    obstacle_data = {
                        "x": obs.get("x", 0),
                        "y": obs.get("y", 0),
                        "type": obs.get("type", "car"),
                        "lane": obs.get("lane", 1),
                        "id": obs.get("id", 0),
                        "color": obs.get("color", None)
                    }
                    current_obstacles.append(obstacle_data)

    except (socket.error, BlockingIOError, OSError) as e:
        if hasattr(e, 'errno') and e.errno in (11, 35, 10035):
            pass
        else:
            print("Socket receive exception:", e)
    except Exception as ex:
        print("Receive loop exception:", ex)

    # interpolate player positions
    for pid, t in targets.items():
        ip = interp.get(pid, {"x": t["x"], "y": t["y"]})
        ip["x"] += (t["x"] - ip["x"]) * 0.3
        ip["y"] += (t["y"] - ip["y"]) * 0.3
        interp[pid] = ip

    # --- DRAWING ---
    screen.fill((0, 160, 0))
    pygame.draw.rect(screen, (50, 50, 50), (ROAD_LEFT, 0, ROAD_WIDTH, SCREEN_H))

    # Draw Lane Markings
    LINE_COLOR = (200, 200, 200)
    LANE_LINES = [ROAD_LEFT + ROAD_WIDTH / 3, ROAD_LEFT + 2 * ROAD_WIDTH / 3]
    DASH_LENGTH = 30
    DASH_GAP = 20
    scroll_offset = int((now * 100) % (DASH_LENGTH + DASH_GAP))

    for line_x in LANE_LINES:
        for y in range(scroll_offset - (DASH_LENGTH + DASH_GAP), SCREEN_H, DASH_LENGTH + DASH_GAP):
            pygame.draw.rect(screen, LINE_COLOR, (line_x - 5, y, 10, DASH_LENGTH))

    # Draw Obstacles (using server-compatible rendering)
    for obs in current_obstacles:
        try:
            x = int(obs["x"])
            y = int(obs["y"])
            obs_type = obs["type"]
            color = obs.get("color")
            
            # Ensure obstacle is drawn within screen bounds
            if 0 <= y <= SCREEN_H:
                draw_obstacle(screen, x, y, obs_type, color)
            
        except Exception as e:
            print(f"Error drawing obstacle: {e}")
            continue

    # Draw Cars and Names
    for pid, ip in interp.items():
        if pid not in targets: 
            continue
            
        x = int(ip["x"])
        y = int(ip["y"])  # Now using server-sent y position
        name = targets[pid]["name"]
        color = COLORS[(pid - 1) % len(COLORS)]
        
        # Only draw if the car is within screen bounds
        if 0 <= y <= SCREEN_H:
            draw_car(screen, x, y, color)

            # Draw name below car
            txt = font.render(name, True, (255, 255, 255))
            screen.blit(txt, (x - txt.get_width()//2, y + 30))

            # Highlight current player
            if player_id is not None and pid == player_id:
                try:
                    pygame.draw.circle(screen, (255, 255, 0), (x, y - 10), 10, 3)
                except Exception:
                    pass

    # --- Display Scoreboard and Timer ---
    timer_text = bold_font.render(f"TIME: {game_time_left:.1f}s", True, (255, 255, 255))
    screen.blit(timer_text, (50, 50))

    # Display controls help
    controls_text = bold_font.render("CONTROLS: ← → Lanes | ↑ ↓ Dodge", True, (255, 255, 200))
    screen.blit(controls_text, (50, SCREEN_H - 80))

    score_y = 50
    header_text = font.render("SCOREBOARD", True, (255, 255, 255))
    screen.blit(header_text, (SCREEN_W - 150, score_y))
    score_y += 30

    sorted_scores = sorted(player_scores.values(), key=lambda x: x['score'], reverse=True)

    for info in sorted_scores:
        name = info["name"]
        score = info["score"]
        status = " (Finished!)" if info["finished"] else ""
        score_text = font.render(f"{name}: {score}{status}", True, (255, 255, 255))
        screen.blit(score_text, (SCREEN_W - 150, score_y))
        score_y += 20

    # Show connection status
    if not join_confirmed:
        if time.time() > join_deadline:
            notice = font.render("Unable to contact server (no join_ack). Check server IP.", True, (255, 200, 0))
        else:
            notice = font.render("Connecting to server...", True, (255, 255, 0))
        screen.blit(notice, (50, SCREEN_H - 50))

    # Draw Finish Line Screen
    if not game_running and sorted_scores and game_time_left == 0:
        winner_info = sorted_scores[0]
        winner_name = winner_info["name"]

        s = pygame.Surface((SCREEN_W, SCREEN_H))
        s.set_alpha(180)
        s.fill((0, 0, 0))
        screen.blit(s, (0, 0))

        finish_text = emoji_font.render("🏁 FINISH LINE! 🏁", True, (255, 255, 50))
        winner_text = large_font.render(f"WINNER: {winner_name}", True, (50, 255, 50))

        screen.blit(finish_text, (SCREEN_W // 2 - finish_text.get_width() // 2, SCREEN_H // 3))
        screen.blit(winner_text, (SCREEN_W // 2 - winner_text.get_width() // 2, SCREEN_H // 3 + 100))

    pygame.display.flip()
    clock.tick(60)

# Clean up
try:
    sock.sendto(json.dumps({"type": "leave"}).encode(), server)
except Exception as ex:
    print("Leave send error:", ex)
pygame.quit()