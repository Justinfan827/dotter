import socket
import json
import threading

BUFFER_SIZE = 4096
DELIMITER = b'\n'

class Server:
    def __init__(self, port=5555):
        self.port = port
        self.conn = None
        self.addr = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.received_data = None
        self.lock = threading.Lock()
        self.running = False

    def start(self):
        """Start server and wait for a client to connect."""
        self.socket.bind(('0.0.0.0', self.port))
        self.socket.listen(1)
        print(f"Server listening on port {self.port}...")
        print("Waiting for player 2 to connect...")
        self.conn, self.addr = self.socket.accept()
        self.conn.setblocking(False)
        print(f"Player 2 connected from {self.addr}")
        self.running = True
        return True

    def send(self, data):
        """Send game state to client."""
        if self.conn:
            try:
                msg = json.dumps(data).encode() + DELIMITER
                self.conn.sendall(msg)
            except (BrokenPipeError, ConnectionResetError):
                self.running = False

    def receive(self):
        """Receive input from client (non-blocking)."""
        if not self.conn:
            return None
        try:
            data = self.conn.recv(BUFFER_SIZE)
            if data:
                # Get the last complete message
                messages = data.split(DELIMITER)
                for msg in reversed(messages):
                    if msg:
                        return json.loads(msg.decode())
        except BlockingIOError:
            pass
        except (json.JSONDecodeError, ConnectionResetError):
            pass
        return None

    def close(self):
        """Close server."""
        self.running = False
        if self.conn:
            self.conn.close()
        self.socket.close()


class Client:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False

    def connect(self, host, port):
        """Connect to server."""
        try:
            self.socket.connect((host, port))
            self.socket.setblocking(False)
            self.running = True
            print(f"Connected to {host}:{port}")
            return True
        except (ConnectionRefusedError, socket.timeout, OSError) as e:
            print(f"Connection failed: {e}")
            return False

    def send(self, data):
        """Send input to server."""
        try:
            msg = json.dumps(data).encode() + DELIMITER
            self.socket.sendall(msg)
        except (BrokenPipeError, ConnectionResetError):
            self.running = False

    def receive(self):
        """Receive game state from server (non-blocking)."""
        try:
            data = self.socket.recv(BUFFER_SIZE)
            if data:
                # Get the last complete message
                messages = data.split(DELIMITER)
                for msg in reversed(messages):
                    if msg:
                        return json.loads(msg.decode())
        except BlockingIOError:
            pass
        except (json.JSONDecodeError, ConnectionResetError):
            self.running = False
        return None

    def close(self):
        """Close connection."""
        self.running = False
        self.socket.close()
