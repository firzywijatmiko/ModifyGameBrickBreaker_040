import math
import random
import pygame

pygame.init()

# ---------------------------------------------------------------- Settings
WIDTH, HEIGHT = 600, 500
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CYAN = (0, 229, 255)
PINK = (255, 80, 160)
YELLOW = (255, 214, 10)
RED = (255, 70, 90)

# Warna tiap baris blok (atas -> bawah)
ROW_COLORS = [
    (255, 71, 87),
    (255, 140, 66),
    (255, 214, 10),
    (46, 213, 115),
    (30, 144, 255),
    (162, 89, 255),
]

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Block Breaker - Neon Edition")
clock = pygame.time.Clock()

font_small = pygame.font.Font(None, 24)
font_medium = pygame.font.Font(None, 36)
font_big = pygame.font.Font(None, 72)


# ---------------------------------------------------------------- Helpers
def make_background():
    """Gradient gelap dari atas ke bawah."""
    bg = pygame.Surface((WIDTH, HEIGHT))
    top, bottom = (12, 10, 40), (40, 12, 70)
    for y in range(HEIGHT):
        t = y / HEIGHT
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        pygame.draw.line(bg, color, (0, y), (WIDTH, y))
    return bg


def lighten(color, amount):
    return tuple(min(255, int(c + (255 - c) * amount)) for c in color)


def darken(color, amount):
    return tuple(max(0, int(c * (1 - amount))) for c in color)


def draw_glow(surface, color, pos, radius, layers=5):
    """Efek cahaya lembut di sekitar objek."""
    size = radius * 6
    glow = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    for i in range(layers, 0, -1):
        r = radius + i * 4
        alpha = int(40 / i + 8)
        pygame.draw.circle(glow, (*color, alpha), (center, center), r)
    surface.blit(glow, (pos[0] - center, pos[1] - center))


def draw_text(surface, text, font, color, center, shadow=True):
    if shadow:
        sh = font.render(text, True, (0, 0, 0))
        surface.blit(sh, sh.get_rect(center=(center[0] + 2, center[1] + 2)))
    img = font.render(text, True, color)
    surface.blit(img, img.get_rect(center=center))


def draw_heart(surface, x, y, size, color):
    r = size // 2
    pygame.draw.circle(surface, color, (x - r // 2, y), r // 2 + 1)
    pygame.draw.circle(surface, color, (x + r // 2, y), r // 2 + 1)
    pygame.draw.polygon(
        surface, color,
        [(x - r - 1, y + 1), (x + r + 1, y + 1), (x, y + r + 4)],
    )


# ---------------------------------------------------------------- Star field
class Star:
    def __init__(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(0, HEIGHT)
        self.speed = random.uniform(0.1, 0.6)
        self.size = random.choice([1, 1, 2])
        self.phase = random.uniform(0, math.pi * 2)

    def update(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.uniform(0, WIDTH)
        self.phase += 0.05

    def draw(self, surface):
        b = int(150 + 100 * math.sin(self.phase))
        pygame.draw.circle(surface, (b, b, b), (int(self.x), int(self.y)), self.size)


# ---------------------------------------------------------------- Particles
class Particle:
    def __init__(self, x, y, color):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1, 4.5)
        self.x, self.y = x, y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.randint(18, 35)
        self.max_life = self.life
        self.color = color
        self.size = random.randint(2, 4)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12
        self.life -= 1

    def draw(self, surface):
        alpha = max(0, int(255 * self.life / self.max_life))
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (self.size, self.size), self.size)
        surface.blit(s, (self.x - self.size, self.y - self.size))


# ---------------------------------------------------------------- Striker
class Striker:
    def __init__(self, posx, posy, width, height, speed, color):
        self.posx, self.posy = posx, posy
        self.width, self.height = width, height
        self.speed = speed
        self.color = color
        self.strikerRect = pygame.Rect(self.posx, self.posy, self.width, self.height)

    def update(self, xFac):
        self.posx += self.speed * xFac
        self.posx = max(0, min(WIDTH - self.width, self.posx))
        self.strikerRect = pygame.Rect(self.posx, self.posy, self.width, self.height)

    def display(self, surface):
        r = self.strikerRect
        draw_glow(surface, CYAN, r.center, 14, layers=3)
        pygame.draw.rect(surface, darken(CYAN, 0.45), r, border_radius=10)
        inner = r.inflate(-4, -4)
        pygame.draw.rect(surface, CYAN, inner, border_radius=8)
        shine = pygame.Rect(inner.x + 6, inner.y + 2, inner.width - 12, 4)
        pygame.draw.rect(surface, lighten(CYAN, 0.7), shine, border_radius=3)

    def getRect(self):
        return self.strikerRect


# ---------------------------------------------------------------- Block
class Block:
    def __init__(self, posx, posy, width, height, color, health):
        self.posx, self.posy = posx, posy
        self.width, self.height = width, height
        self.color = color
        self.max_health = health
        self.health = health
        self.damage = 1
        self.flash = 0
        self.blockRect = pygame.Rect(self.posx, self.posy, self.width, self.height)

    def display(self, surface):
        if self.health <= 0:
            return
        r = self.blockRect
        base = self.color
        if self.flash > 0:
            base = lighten(base, 0.6)
            self.flash -= 1
        pygame.draw.rect(surface, darken(base, 0.45), r, border_radius=5)
        inner = r.inflate(-3, -3)
        pygame.draw.rect(surface, base, inner, border_radius=4)
        shine = pygame.Rect(inner.x + 3, inner.y + 2, inner.width - 6, 4)
        pygame.draw.rect(surface, lighten(base, 0.5), shine, border_radius=2)

        # blok kuat: tampilkan bingkai emas selama masih utuh
        if self.max_health > 1 and self.health == self.max_health:
            pygame.draw.rect(surface, (255, 255, 255), r, width=2, border_radius=5)
        elif self.health < self.max_health:
            # retakan
            c = darken(base, 0.6)
            pygame.draw.line(surface, c, (r.x + 8, r.y + 3), (r.centerx, r.bottom - 4), 2)
            pygame.draw.line(surface, c, (r.centerx, r.bottom - 4), (r.right - 8, r.y + 4), 2)

    def hit(self):
        self.health -= self.damage
        self.flash = 4

    def getRect(self):
        return self.blockRect

    def getHealth(self):
        return self.health


# ---------------------------------------------------------------- Ball
class Ball:
    def __init__(self, posx, posy, radius, speed, color):
        self.posx, self.posy = posx, posy
        self.radius = radius
        self.base_speed = speed
        self.speed = speed
        self.color = color
        self.vx, self.vy = speed * 0.6, -speed * 0.8
        self.trail = []

    def update(self):
        """Gerakkan bola. Return True jika bola jatuh."""
        self.trail.append((self.posx, self.posy))
        if len(self.trail) > 12:
            self.trail.pop(0)

        self.posx += self.vx
        self.posy += self.vy

        if self.posx - self.radius <= 0:
            self.posx = self.radius
            self.vx = abs(self.vx)
        elif self.posx + self.radius >= WIDTH:
            self.posx = WIDTH - self.radius
            self.vx = -abs(self.vx)

        if self.posy - self.radius <= 0:
            self.posy = self.radius
            self.vy = abs(self.vy)

        return self.posy - self.radius >= HEIGHT

    def stick_to(self, striker):
        self.posx = striker.getRect().centerx
        self.posy = striker.getRect().top - self.radius - 1
        self.trail.clear()

    def launch(self):
        angle = math.radians(random.uniform(-25, 25))
        self.vx = self.speed * math.sin(angle)
        self.vy = -self.speed * math.cos(angle)

    def bounce_striker(self, striker_rect):
        """Sudut pantul tergantung posisi bola di striker."""
        offset = (self.posx - striker_rect.centerx) / (striker_rect.width / 2)
        offset = max(-1, min(1, offset))
        angle = offset * math.radians(60)
        self.vx = self.speed * math.sin(angle)
        self.vy = -self.speed * math.cos(angle)
        self.posy = striker_rect.top - self.radius - 1

    def display(self, surface):
        # jejak
        for i, (tx, ty) in enumerate(self.trail):
            t = (i + 1) / len(self.trail)
            r = max(1, int(self.radius * t * 0.8))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*PINK, int(110 * t)), (r, r), r)
            surface.blit(s, (tx - r, ty - r))
        draw_glow(surface, PINK, (int(self.posx), int(self.posy)), self.radius, layers=4)
        pygame.draw.circle(surface, PINK, (int(self.posx), int(self.posy)), self.radius)
        pygame.draw.circle(
            surface, WHITE, (int(self.posx - 2), int(self.posy - 2)), max(2, self.radius // 3)
        )

    def getRect(self):
        return pygame.Rect(
            self.posx - self.radius, self.posy - self.radius,
            self.radius * 2, self.radius * 2,
        )


# ---------------------------------------------------------------- Game functions
def collisionChecker(rect, ball_rect):
    return rect.colliderect(ball_rect)


def populateBlocks(blockWidth, blockHeight, horizontalGap, verticalGap, rows=6):
    listOfBlocks = []
    cols = 10
    total_w = cols * blockWidth + (cols - 1) * horizontalGap
    start_x = (WIDTH - total_w) // 2
    start_y = 60
    for row in range(rows):
        for col in range(cols):
            x = start_x + col * (blockWidth + horizontalGap)
            y = start_y + row * (blockHeight + verticalGap)
            health = 2 if row < 2 else 1
            listOfBlocks.append(
                Block(x, y, blockWidth, blockHeight, ROW_COLORS[row % len(ROW_COLORS)], health)
            )
    return listOfBlocks


def draw_hud(surface, score, lives, level):
    bar = pygame.Surface((WIDTH, 34), pygame.SRCALPHA)
    bar.fill((0, 0, 0, 120))
    surface.blit(bar, (0, 0))
    pygame.draw.line(surface, (90, 70, 160), (0, 34), (WIDTH, 34), 1)

    draw_text(surface, f"SCORE  {score}", font_small, WHITE, (75, 17), shadow=False)
    draw_text(surface, f"LEVEL {level}", font_small, YELLOW, (WIDTH // 2, 17), shadow=False)
    for i in range(lives):
        draw_heart(surface, WIDTH - 24 - i * 26, 14, 14, RED)


def overlay(surface, title, subtitle, hint, title_color):
    dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dark.fill((0, 0, 0, 160))
    surface.blit(dark, (0, 0))
    draw_text(surface, title, font_big, title_color, (WIDTH // 2, HEIGHT // 2 - 50))
    draw_text(surface, subtitle, font_medium, WHITE, (WIDTH // 2, HEIGHT // 2 + 10))
    blink = (pygame.time.get_ticks() // 500) % 2 == 0
    if blink:
        draw_text(surface, hint, font_small, CYAN, (WIDTH // 2, HEIGHT // 2 + 60))


# ---------------------------------------------------------------- Main
def main():
    background = make_background()
    stars = [Star() for _ in range(70)]
    particles = []

    lives, score, level = 3, 0, 1
    state = "ready"  # ready | playing | gameover
    shake = 0

    striker = Striker(WIDTH // 2 - 50, HEIGHT - 40, 100, 16, 8, CYAN)
    ball = Ball(WIDTH // 2, HEIGHT - 60, 7, 5.5, WHITE)
    ball.stick_to(striker)

    blockWidth, blockHeight = 50, 18
    horizontalGap, verticalGap = 6, 6
    listOfBlocks = populateBlocks(blockWidth, blockHeight, horizontalGap, verticalGap)

    world = pygame.Surface((WIDTH, HEIGHT))
    running = True

    while running:
        # ---------- events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    if state == "ready":
                        ball.launch()
                        state = "playing"
                    elif state == "gameover":
                        lives, score, level = 3, 0, 1
                        ball.speed = ball.base_speed
                        listOfBlocks = populateBlocks(
                            blockWidth, blockHeight, horizontalGap, verticalGap
                        )
                        ball.stick_to(striker)
                        state = "ready"

        keys = pygame.key.get_pressed()
        xFac = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            xFac -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            xFac += 1

        # ---------- update
        for s in stars:
            s.update()

        if state != "gameover":
            striker.update(xFac)

        if state == "ready":
            ball.stick_to(striker)

        elif state == "playing":
            lifeLost = ball.update()

            # striker
            if ball.vy > 0 and collisionChecker(striker.getRect(), ball.getRect()):
                ball.bounce_striker(striker.getRect())

            # blok
            ball_rect = ball.getRect()
            for block in listOfBlocks:
                if collisionChecker(block.getRect(), ball_rect):
                    br = block.getRect()
                    overlap_x = min(ball_rect.right - br.left, br.right - ball_rect.left)
                    overlap_y = min(ball_rect.bottom - br.top, br.bottom - ball_rect.top)
                    if overlap_x < overlap_y:
                        ball.vx *= -1
                    else:
                        ball.vy *= -1
                    block.hit()
                    if block.getHealth() <= 0:
                        score += 10 * level
                        for _ in range(16):
                            particles.append(Particle(br.centerx, br.centery, block.color))
                    else:
                        score += 2
                        for _ in range(4):
                            particles.append(Particle(ball.posx, ball.posy, WHITE))
                    break

            listOfBlocks = [b for b in listOfBlocks if b.getHealth() > 0]

            # level baru
            if not listOfBlocks:
                level += 1
                ball.speed = min(ball.base_speed + level * 0.5, 9)
                listOfBlocks = populateBlocks(
                    blockWidth, blockHeight, horizontalGap, verticalGap
                )
                state = "ready"
                ball.stick_to(striker)

            # nyawa hilang
            if lifeLost:
                lives -= 1
                shake = 12
                if lives <= 0:
                    state = "gameover"
                else:
                    state = "ready"
                    ball.stick_to(striker)

        for p in particles:
            p.update()
        particles = [p for p in particles if p.life > 0]

        # ---------- draw
        world.blit(background, (0, 0))
        for s in stars:
            s.draw(world)
        for block in listOfBlocks:
            block.display(world)
        striker.display(world)
        ball.display(world)
        for p in particles:
            p.draw(world)
        draw_hud(world, score, lives, level)

        if state == "ready":
            draw_text(world, "Tekan SPASI untuk meluncurkan bola", font_small, WHITE,
                      (WIDTH // 2, HEIGHT - 80))
        elif state == "gameover":
            overlay(world, "GAME OVER", f"Skor akhir: {score}",
                    "Tekan SPASI untuk main lagi", RED)

        # screen shake
        ox = oy = 0
        if shake > 0:
            ox, oy = random.randint(-4, 4), random.randint(-4, 4)
            shake -= 1
        screen.fill(BLACK)
        screen.blit(world, (ox, oy))

        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()