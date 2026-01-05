import pygame
import time
import random
from network import Server, Client

# Initialize
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dot Dodger")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 72)
small_font = pygame.font.Font(None, 28)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
GREEN = (100, 255, 100)
RED = (255, 80, 80)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 100)
PURPLE = (150, 100, 200)

PORT = 5555


class Obstacle:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = PURPLE

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height), 2)

    def to_dict(self):
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}

    @staticmethod
    def from_dict(data):
        return Obstacle(data["x"], data["y"], data["width"], data["height"])


class Player:
    def __init__(self, x, y, color, start_x=None, start_y=None):
        self.x = x
        self.y = y
        self.start_x = start_x if start_x else x
        self.start_y = start_y if start_y else y
        self.color = color
        self.radius = 15
        self.speed = 5
        self.alive = True
        self.lives = 3  # Default, will be set by game

    def respawn(self):
        """Reset position after being hit."""
        self.x = self.start_x
        self.y = self.start_y
        self.alive = True

    def move_with_keys(self, keys, obstacles=None):
        if not self.alive:
            return
        
        old_x, old_y = self.x, self.y
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed
        
        # Check boundaries
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))
        
        # Check obstacle collisions
        if obstacles:
            for obstacle in obstacles:
                if check_circle_rect_collision(self, obstacle):
                    self.x, self.y = old_x, old_y
                    break

    def move_with_input(self, input_data, obstacles=None):
        """Move based on network input data."""
        if not self.alive or not input_data:
            return
        
        old_x, old_y = self.x, self.y
        keys = input_data.get("keys", {})
        if keys.get("left"):
            self.x -= self.speed
        if keys.get("right"):
            self.x += self.speed
        if keys.get("up"):
            self.y -= self.speed
        if keys.get("down"):
            self.y += self.speed
        
        # Check boundaries
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))
        
        # Check obstacle collisions
        if obstacles:
            for obstacle in obstacles:
                if check_circle_rect_collision(self, obstacle):
                    self.x, self.y = old_x, old_y
                    break

    def draw(self):
        if self.alive:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def to_dict(self):
        return {"x": self.x, "y": self.y, "alive": self.alive, "lives": self.lives}

    def from_dict(self, data):
        self.x = data["x"]
        self.y = data["y"]
        self.alive = data["alive"]
        self.lives = data.get("lives", self.lives)


class Bullet:
    def __init__(self, x, y, target_x, target_y, owner):
        self.x = x
        self.y = y
        self.radius = 5
        self.speed = 10
        self.owner = owner  # 0 = player 1, 1 = player 2
        dx = target_x - x
        dy = target_y - y
        dist = max((dx**2 + dy**2) ** 0.5, 1)
        self.vx = (dx / dist) * self.speed
        self.vy = (dy / dist) * self.speed

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def draw(self):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius)

    def off_screen(self):
        return self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT
    
    def hits_obstacle(self, obstacles):
        if obstacles:
            for obstacle in obstacles:
                if check_circle_rect_collision(self, obstacle):
                    return True
        return False

    def to_dict(self):
        return {"x": self.x, "y": self.y, "vx": self.vx, "vy": self.vy, "owner": self.owner}

    @staticmethod
    def from_dict(data):
        b = Bullet(data["x"], data["y"], data["x"] + data["vx"], data["y"] + data["vy"], data["owner"])
        b.vx = data["vx"]
        b.vy = data["vy"]
        return b


def check_collision(obj1, obj2):
    dx = obj1.x - obj2.x
    dy = obj1.y - obj2.y
    dist = (dx**2 + dy**2) ** 0.5
    return dist < obj1.radius + obj2.radius


def check_circle_rect_collision(circle, rect):
    closest_x = max(rect.x, min(circle.x, rect.x + rect.width))
    closest_y = max(rect.y, min(circle.y, rect.y + rect.height))
    dx = circle.x - closest_x
    dy = circle.y - closest_y
    return (dx * dx + dy * dy) < (circle.radius * circle.radius)


def generate_obstacles(num_obstacles=8):
    obstacles = []
    min_size = 40
    max_size = 100
    margin = 100
    
    attempts = 0
    while len(obstacles) < num_obstacles and attempts < 1000:
        width = random.randint(min_size, max_size)
        height = random.randint(min_size, max_size)
        x = random.randint(margin, WIDTH - width - margin)
        y = random.randint(margin, HEIGHT - height - margin)
        
        new_obstacle = Obstacle(x, y, width, height)
        
        # Check if obstacle blocks player starting positions
        player1_start = (200, HEIGHT // 2)
        player2_start = (WIDTH - 200, HEIGHT // 2)
        
        valid = True
        
        # Check if obstacle overlaps with player starting areas
        for px, py in [player1_start, player2_start]:
            player_circle = type('Player', (), {'x': px, 'y': py, 'radius': 30})
            if check_circle_rect_collision(player_circle, new_obstacle):
                valid = False
                break
        
        # Check if obstacle overlaps with other obstacles
        for obs in obstacles:
            if (new_obstacle.x < obs.x + obs.width and
                new_obstacle.x + new_obstacle.width > obs.x and
                new_obstacle.y < obs.y + obs.height and
                new_obstacle.y + new_obstacle.height > obs.y):
                valid = False
                break
        
        if valid:
            obstacles.append(new_obstacle)
        
        attempts += 1
    
    return obstacles


def show_main_menu():
    """Show main menu with game mode selection."""
    while True:
        screen.fill(BLACK)
        title = big_font.render("DOT DODGER", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))

        subtitle = font.render("PvP Edition", True, GRAY)
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 190))

        instructions = [
            "",
            "Press 1 for SINGLE PLAYER",
            "Press 2 to HOST GAME",
            "Press 3 to JOIN GAME",
            "",
            "Arrow keys or WASD to move",
            "SPACE to shoot toward mouse",
            "ESC to quit",
        ]
        for i, line in enumerate(instructions):
            color = GRAY if line == "" else WHITE
            text = font.render(line, True, color)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 240 + i * 35))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None, None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "single", None
                if event.key == pygame.K_2:
                    return "host", None
                if event.key == pygame.K_3:
                    return "join", None
                if event.key == pygame.K_ESCAPE:
                    return None, None
        clock.tick(60)


def select_lives():
    """Let the user select number of lives."""
    while True:
        screen.fill(BLACK)
        title = font.render("SELECT NUMBER OF LIVES", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))

        options = [
            "",
            "Press 1 for 1 LIFE",
            "Press 2 for 2 LIVES",
            "Press 3 for 3 LIVES",
            "Press 4 for 5 LIVES",
            "Press 5 for 10 LIVES",
            "",
            "ESC to go back",
        ]
        for i, line in enumerate(options):
            color = GRAY if line == "" else WHITE
            text = font.render(line, True, color)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 220 + i * 40))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return 1
                if event.key == pygame.K_2:
                    return 2
                if event.key == pygame.K_3:
                    return 3
                if event.key == pygame.K_4:
                    return 5
                if event.key == pygame.K_5:
                    return 10
                if event.key == pygame.K_ESCAPE:
                    return "back"
        clock.tick(60)


def get_join_address():
    """Get server address from user input."""
    input_text = ""
    while True:
        screen.fill(BLACK)
        title = font.render("JOIN GAME", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))

        prompt = font.render("Enter host address (e.g., 0.tcp.ngrok.io:12345):", True, GRAY)
        screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 250))

        # Input box
        input_surface = font.render(input_text + "_", True, WHITE)
        pygame.draw.rect(screen, GRAY, (100, 300, 600, 40), 2)
        screen.blit(input_surface, (110, 308))

        hint = small_font.render("Press ENTER to connect, ESC to go back", True, GRAY)
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 380))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "back"
                if event.key == pygame.K_RETURN:
                    return input_text
                if event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                # Paste with Cmd+V (Mac) or Ctrl+V
                elif event.key == pygame.K_v and (event.mod & pygame.KMOD_META or event.mod & pygame.KMOD_CTRL):
                    try:
                        import subprocess
                        paste = subprocess.run(['pbpaste'], capture_output=True, text=True).stdout.strip()
                        input_text += paste
                    except:
                        pass
                elif event.unicode.isprintable():
                    input_text += event.unicode
        clock.tick(60)


def show_waiting_screen(message):
    """Show a waiting screen with a message."""
    screen.fill(BLACK)
    text = font.render(message, True, WHITE)
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
    hint = small_font.render("Press ESC to cancel", True, GRAY)
    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 50))
    pygame.display.flip()


def show_result_screen(won):
    """Show win/lose screen."""
    while True:
        screen.fill(BLACK)
        if won:
            title = big_font.render("YOU WIN!", True, GREEN)
        else:
            title = big_font.render("YOU LOSE!", True, RED)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 200))

        restart_text = font.render("Press R to play again or ESC to quit", True, GRAY)
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, 320))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False
        clock.tick(60)


def get_local_input():
    """Get current keyboard state as input dict."""
    keys = pygame.key.get_pressed()
    return {
        "keys": {
            "left": keys[pygame.K_LEFT] or keys[pygame.K_a],
            "right": keys[pygame.K_RIGHT] or keys[pygame.K_d],
            "up": keys[pygame.K_UP] or keys[pygame.K_w],
            "down": keys[pygame.K_DOWN] or keys[pygame.K_s],
        },
        "shoot": None,
    }


def run_single_player(num_lives):
    """Single player mode - you vs AI (simple bot)."""
    player1 = Player(200, HEIGHT // 2, BLUE)
    player2 = Player(WIDTH - 200, HEIGHT // 2, GREEN)  # Bot
    player1.lives = num_lives
    player2.lives = num_lives
    bullets = []
    obstacles = generate_obstacles()
    last_bot_shot = time.time()
    respawn_time = None  # Track respawn delay

    while True:
        shoot_target = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key == pygame.K_SPACE and player1.alive:
                    mx, my = pygame.mouse.get_pos()
                    shoot_target = (mx, my)

        # Handle respawn delay
        if respawn_time and time.time() - respawn_time > 1.0:
            if not player1.alive and player1.lives > 0:
                player1.respawn()
            if not player2.alive and player2.lives > 0:
                player2.respawn()
            respawn_time = None
            bullets = []  # Clear bullets on respawn

        # Player 1 input
        keys = pygame.key.get_pressed()
        player1.move_with_keys(keys, obstacles)

        if shoot_target:
            bullets.append(Bullet(player1.x, player1.y, shoot_target[0], shoot_target[1], 0))

        # Bot AI - simple: move toward player, shoot periodically
        if player2.alive and player1.alive:
            dx = player1.x - player2.x
            dy = player1.y - player2.y
            dist = max((dx**2 + dy**2) ** 0.5, 1)
            player2.x += (dx / dist) * 2  # Slower than player
            player2.y += (dy / dist) * 2
            player2.x = max(player2.radius, min(WIDTH - player2.radius, player2.x))
            player2.y = max(player2.radius, min(HEIGHT - player2.radius, player2.y))

            # Bot shoots every 1.5 seconds
            if time.time() - last_bot_shot > 1.5:
                bullets.append(Bullet(player2.x, player2.y, player1.x, player1.y, 1))
                last_bot_shot = time.time()

        # Update bullets
        for bullet in bullets:
            bullet.update()
        bullets = [b for b in bullets if not b.off_screen() and not b.hits_obstacle(obstacles)]

        # Check bullet-player collisions
        for bullet in bullets[:]:
            if bullet.owner == 0 and player2.alive and check_collision(bullet, player2):
                player2.lives -= 1
                player2.alive = False
                bullets.remove(bullet)
                if player2.lives > 0:
                    respawn_time = time.time()
            elif bullet.owner == 1 and player1.alive and check_collision(bullet, player1):
                player1.lives -= 1
                player1.alive = False
                bullets.remove(bullet)
                if player1.lives > 0:
                    respawn_time = time.time()

        # Check win condition
        if player1.lives <= 0 and not player1.alive:
            return False  # You lose
        if player2.lives <= 0 and not player2.alive:
            return True  # You win

        # Draw
        screen.fill(BLACK)
        for obstacle in obstacles:
            obstacle.draw()
        player1.draw()
        player2.draw()
        for bullet in bullets:
            bullet.draw()

        p1_text = font.render(f"P1 (Blue) - Lives: {player1.lives}", True, BLUE)
        p2_text = font.render(f"YOU (Green) - Lives: {player2.lives}", True, GREEN)
        screen.blit(p1_text, (10, 10))
        screen.blit(p2_text, (WIDTH - p2_text.get_width() - 10, 10))

        pygame.display.flip()
        clock.tick(60)

    client.close()
    return None


def main():
    import socket as socket_module
    global socket
    socket = socket_module

    while True:
        mode, _ = show_main_menu()
        if mode is None:
            break

        # For host and single player, select lives
        num_lives = 3  # Default
        if mode in ("single", "host"):
            lives_result = select_lives()
            if lives_result is None:
                break
            if lives_result == "back":
                continue
            num_lives = lives_result

        result = None

        if mode == "single":
            result = run_single_player(num_lives)
        elif mode == "host":
            result = run_host_game(num_lives)
        elif mode == "join":
            address = get_join_address()
            if address is None:
                break
            if address == "back":
                continue
            result = run_join_game(address)

        if result is None:
            continue

        if not show_result_screen(result):
            break

    pygame.quit()


if __name__ == "__main__":
    main()
