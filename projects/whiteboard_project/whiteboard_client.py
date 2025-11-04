# whiteboard_client.py
import socket
import threading
import tkinter as tk
from tkinter import simpledialog, colorchooser, messagebox
import json

TCP_PORT = 5000
UDP_PORT = 6000
BUFFER = 4096

# --- GUI popups for server IP and username (works when run as .exe without console) ---
root = tk.Tk()
root.withdraw()
server_ip = simpledialog.askstring("Server IP", "Enter server IP (leave blank for localhost):")
if not server_ip:
    server_ip = "localhost"
username = simpledialog.askstring("Username", "Enter your username:")
if not username:
    username = "User"
root.destroy()

# --- TCP setup (chat & control) ---
tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    tcp.connect((server_ip, TCP_PORT))
except Exception as e:
    messagebox.showerror("Connection failed", f"Could not connect to server: {e}")
    raise SystemExit

# Send initial hello with username
hello = {"type":"hello","username": username}
tcp.sendall(json.dumps(hello).encode('utf-8'))

# --- UDP setup (drawing) ---
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp.bind(("", 0))   # bind to ephemeral port so we can receive forwarded UDP

# on startup send a small UDP ping so server learns our UDP addr
udp.sendto(b'{"type":"hello_udp"}', (server_ip, UDP_PORT))

# --- GUI layout ---
app = tk.Tk()
app.title(f"Shared Whiteboard - {username}")
app.geometry("1000x700")

# Top toolbar
toolbar = tk.Frame(app)
toolbar.pack(side=tk.TOP, fill=tk.X)

btn_color = tk.Button(toolbar, text="Color")
btn_color.pack(side=tk.LEFT, padx=4, pady=4)
btn_eraser = tk.Button(toolbar, text="Eraser")
btn_eraser.pack(side=tk.LEFT, padx=4, pady=4)
tk.Label(toolbar, text="Stroke:").pack(side=tk.LEFT, padx=(8,0))
stroke_slider = tk.Scale(toolbar, from_=1, to=25, orient=tk.HORIZONTAL)
stroke_slider.set(3)
stroke_slider.pack(side=tk.LEFT, padx=4)
btn_clear = tk.Button(toolbar, text="Clear")
btn_clear.pack(side=tk.RIGHT, padx=8)

# Canvas
canvas = tk.Canvas(app, bg="white", width=900, height=520)
canvas.pack(padx=8, pady=6)

# Chat area
chat_frame = tk.Frame(app)
chat_frame.pack(fill=tk.X, padx=8, pady=(0,8))
chat_text = tk.Text(chat_frame, height=6, state=tk.DISABLED)
chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
chat_entry = tk.Entry(chat_frame)
chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=False, padx=(6,0))
btn_send = tk.Button(chat_frame, text="Send")
btn_send.pack(side=tk.LEFT, padx=6)

# state
current_color = "#000000"
eraser_on = False
drawing = False
last_x = last_y = None

# --- functions ---
def choose_color():
    global current_color, eraser_on
    col = colorchooser.askcolor()[1]
    if col:
        current_color = col
        eraser_on = False

def toggle_eraser():
    global eraser_on
    eraser_on = not eraser_on
    btn_eraser.config(relief=tk.SUNKEN if eraser_on else tk.RAISED)

def clear_all():
    # local clear
    canvas.delete("all")
    # notify server via TCP and also via UDP
    try:
        tcp.sendall(json.dumps({"type":"control","action":"clear"}).encode('utf-8'))
    except:
        pass
    try:
        udp.sendto(json.dumps({"type":"control","action":"clear"}).encode('utf-8'), (server_ip, UDP_PORT))
    except:
        pass

def send_chat():
    txt = chat_entry.get().strip()
    if not txt:
        return
    msg = {"type":"chat","user":username,"msg":txt}
    try:
        tcp.sendall(json.dumps(msg).encode('utf-8'))
    except:
        pass
    chat_entry.delete(0, tk.END)

def on_canvas_down(e):
    global drawing, last_x, last_y
    drawing = True
    last_x, last_y = e.x, e.y

def on_canvas_move(e):
    global last_x, last_y
    if not drawing:
        return
    x, y = e.x, e.y
    col = "white" if eraser_on else current_color
    w = stroke_slider.get()
    canvas.create_line(last_x, last_y, x, y, fill=col, width=w, capstyle=tk.ROUND, smooth=True)
    # send UDP JSON
    payload = {"type":"draw","user":username,"color":col,"width":w,"x1":last_x,"y1":last_y,"x2":x,"y2":y}
    try:
        udp.sendto(json.dumps(payload).encode('utf-8'), (server_ip, UDP_PORT))
    except:
        pass
    last_x, last_y = x, y

def on_canvas_up(e):
    global drawing
    drawing = False

def append_chat_line(line):
    chat_text.config(state=tk.NORMAL)
    chat_text.insert(tk.END, line + "\n")
    chat_text.config(state=tk.DISABLED)
    chat_text.see(tk.END)

# --- network receiver threads ---
def tcp_receiver():
    while True:
        try:
            data = tcp.recv(BUFFER)
            if not data:
                break
            try:
                obj = json.loads(data.decode('utf-8'))
            except:
                continue
            if obj.get("type") == "chat":
                u = obj.get("user","")
                m = obj.get("msg","")
                append_chat_line(f"{u}: {m}")
            elif obj.get("type") == "system":
                append_chat_line(f"[SYSTEM] {obj.get('msg','')}")
            elif obj.get("type") == "control" and obj.get("action")=="clear":
                canvas.delete("all")
        except:
            break

def udp_receiver():
    while True:
        try:
            data, addr = udp.recvfrom(65535)
            if not data:
                continue
            try:
                obj = json.loads(data.decode('utf-8'))
            except:
                continue
            t = obj.get("type")
            if t == "draw":
                x1 = obj.get("x1"); y1 = obj.get("y1"); x2 = obj.get("x2"); y2 = obj.get("y2")
                col = obj.get("color"); w = obj.get("width")
                canvas.create_line(x1, y1, x2, y2, fill=col, width=w, capstyle=tk.ROUND, smooth=True)
            elif t == "control" and obj.get("action")=="clear":
                canvas.delete("all")
            elif t == "hello_udp":
                # no-op, server only uses it to register addr
                pass
        except:
            break

# --- bindings & button wiring ---
canvas.bind("<ButtonPress-1>", on_canvas_down)
canvas.bind("<B1-Motion>", on_canvas_move)
canvas.bind("<ButtonRelease-1>", on_canvas_up)

btn_color.config(command=choose_color)
btn_eraser.config(command=toggle_eraser)
btn_clear.config(command=clear_all)
btn_send.config(command=send_chat)
chat_entry.bind("<Return>", lambda e: send_chat())

# send a UDP hello to register at server
try:
    udp.sendto(json.dumps({"type":"hello_udp"}).encode('utf-8'), (server_ip, UDP_PORT))
except:
    pass

# start receivers
threading.Thread(target=tcp_receiver, daemon=True).start()
threading.Thread(target=udp_receiver, daemon=True).start()

# start GUI
app.mainloop()

# cleanup sockets on exit
try:
    tcp.close()
    udp.close()
except:
    pass
