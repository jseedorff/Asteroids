import math
import random

import pygame

import sound

WIDTH, HEIGHT = 800, 600
FPS = 60

SHIP_TURN_SPEED = 4.0
SHIP_THRUST = 0.25
SHIP_FRICTION = 0.99
BULLET_SPEED = 9
BULLET_LIFETIME = 40
SHOOT_COOLDOWN = 15

ASTEROID_SPEEDS = {"large": 1.2, "medium": 2.0, "small": 3.0}
ASTEROID_RADII = {"large": 40, "medium": 22, "small": 12}
ASTEROID_SCORES = {"large": 20, "medium": 50, "small": 100}

UFO_SPEED = 2.5
UFO_RADIUS = 16
UFO_SCORE = 200
UFO_SHOOT_COOLDOWN_RANGE = (60, 110)
UFO_SPAWN_DELAY_RANGE = (FPS * 6, FPS * 12)
UFO_BULLET_SPEED = 6
UFO_BULLET_LIFETIME = 70
UFO_BULLET_SPREAD = 18  # degrees of random inaccuracy

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 40, 40)
ORANGE = (240, 140, 40)


def wrap_position(pos):
    x, y = pos
    return pygame.Vector2(x % WIDTH, y % HEIGHT)


class Ship:
    def __init__(self):
        self.pos = pygame.Vector2(WIDTH / 2, HEIGHT / 2)
        self.vel = pygame.Vector2(0, 0)
        self.angle = -90  # degrees, pointing up
        self.radius = 12
        self.alive = True
        self.shoot_timer = 0

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle -= SHIP_TURN_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle += SHIP_TURN_SPEED

        thrusting = keys[pygame.K_UP] or keys[pygame.K_w]
        if thrusting:
            direction = pygame.Vector2(math.cos(math.radians(self.angle)), math.sin(math.radians(self.angle)))
            self.vel += direction * SHIP_THRUST

        self.vel *= SHIP_FRICTION
        self.pos = wrap_position(self.pos + self.vel)

        if self.shoot_timer > 0:
            self.shoot_timer -= 1

        return thrusting

    def points(self):
        # Triangle pointing in the direction of self.angle
        forward = pygame.Vector2(math.cos(math.radians(self.angle)), math.sin(math.radians(self.angle)))
        right = pygame.Vector2(-forward.y, forward.x)
        tip = self.pos + forward * self.radius
        left_back = self.pos - forward * self.radius - right * (self.radius * 0.7)
        right_back = self.pos - forward * self.radius + right * (self.radius * 0.7)
        return [tip, left_back, right_back]

    def can_shoot(self):
        return self.shoot_timer <= 0

    def shoot(self):
        self.shoot_timer = SHOOT_COOLDOWN
        direction = pygame.Vector2(math.cos(math.radians(self.angle)), math.sin(math.radians(self.angle)))
        return Bullet(self.pos + direction * self.radius, direction)


class Bullet:
    def __init__(self, pos, direction, speed=BULLET_SPEED, life=BULLET_LIFETIME, color=WHITE):
        self.pos = pygame.Vector2(pos)
        self.vel = direction * speed
        self.life = life
        self.color = color

    def update(self):
        self.pos = wrap_position(self.pos + self.vel)
        self.life -= 1

    def is_dead(self):
        return self.life <= 0


class UFO:
    def __init__(self):
        self.radius = UFO_RADIUS
        side = random.choice(["left", "right"])
        y = random.uniform(50, HEIGHT - 50)
        if side == "left":
            self.pos = pygame.Vector2(-self.radius * 2, y)
            self.vel = pygame.Vector2(UFO_SPEED, 0)
        else:
            self.pos = pygame.Vector2(WIDTH + self.radius * 2, y)
            self.vel = pygame.Vector2(-UFO_SPEED, 0)
        self.bob_phase = random.uniform(0, math.tau)
        self.shoot_timer = random.randint(*UFO_SHOOT_COOLDOWN_RANGE)

    def update(self):
        self.bob_phase += 0.05
        self.pos.x += self.vel.x
        self.pos.y += math.sin(self.bob_phase) * 0.6
        if self.shoot_timer > 0:
            self.shoot_timer -= 1

    def offscreen(self):
        return self.pos.x < -self.radius * 3 or self.pos.x > WIDTH + self.radius * 3

    def can_shoot(self):
        return self.shoot_timer <= 0

    def shoot(self, target_pos):
        self.shoot_timer = random.randint(*UFO_SHOOT_COOLDOWN_RANGE)
        direction = pygame.Vector2(target_pos) - self.pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        direction = direction.normalize().rotate(random.uniform(-UFO_BULLET_SPREAD, UFO_BULLET_SPREAD))
        return Bullet(self.pos, direction, speed=UFO_BULLET_SPEED, life=UFO_BULLET_LIFETIME, color=ORANGE)


class Asteroid:
    def __init__(self, pos=None, size="large"):
        self.size = size
        self.radius = ASTEROID_RADII[size]
        if pos is None:
            pos = self._random_edge_position()
        self.pos = pygame.Vector2(pos)

        angle = random.uniform(0, 360)
        speed = ASTEROID_SPEEDS[size] * random.uniform(0.7, 1.3)
        self.vel = pygame.Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle))) * speed

        # Precompute a jagged shape (offsets from center) so it looks like a rock, not a circle.
        self.shape_offsets = []
        num_points = random.randint(8, 12)
        for i in range(num_points):
            point_angle = (360 / num_points) * i
            distance = self.radius * random.uniform(0.75, 1.15)
            self.shape_offsets.append((point_angle, distance))

    def _random_edge_position(self):
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":
            return (random.uniform(0, WIDTH), 0)
        if side == "bottom":
            return (random.uniform(0, WIDTH), HEIGHT)
        if side == "left":
            return (0, random.uniform(0, HEIGHT))
        return (WIDTH, random.uniform(0, HEIGHT))

    def update(self):
        self.pos = wrap_position(self.pos + self.vel)

    def points(self):
        pts = []
        for angle, distance in self.shape_offsets:
            rad = math.radians(angle)
            pts.append((self.pos.x + math.cos(rad) * distance, self.pos.y + math.sin(rad) * distance))
        return pts

    def split(self):
        if self.size == "large":
            return [Asteroid(self.pos, "medium") for _ in range(2)]
        if self.size == "medium":
            return [Asteroid(self.pos, "small") for _ in range(2)]
        return []


class Particle:
    def __init__(self, pos, vel, life, color=WHITE):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.life = life
        self.max_life = life
        self.color = color

    def update(self):
        self.pos = wrap_position(self.pos + self.vel)
        self.vel *= 0.97
        self.life -= 1

    def is_dead(self):
        return self.life <= 0

    def draw(self, surface):
        # Fade the particle toward black as it ages, and shrink it.
        t = self.life / self.max_life
        color = tuple(int(c * t) for c in self.color)
        radius = max(1, round(3 * t))
        pygame.draw.circle(surface, color, self.pos, radius)


def spawn_explosion(pos, count=20, speed_range=(1, 5), lifetime_range=(20, 45), color=WHITE):
    particles = []
    for _ in range(count):
        angle = random.uniform(0, 360)
        speed = random.uniform(*speed_range)
        vel = pygame.Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle))) * speed
        life = random.randint(*lifetime_range)
        particles.append(Particle(pos, vel, life, color))
    return particles


def distance(a, b):
    return (pygame.Vector2(a) - pygame.Vector2(b)).length()


def spawn_wave(count):
    return [Asteroid(size="large") for _ in range(count)]


def draw_ship(surface, ship, thrusting):
    pygame.draw.polygon(surface, WHITE, ship.points(), width=2)
    if thrusting:
        forward = pygame.Vector2(math.cos(math.radians(ship.angle)), math.sin(math.radians(ship.angle)))
        flame_tip = ship.pos - forward * (ship.radius * 1.6)
        back_left, back_right = ship.points()[1], ship.points()[2]
        pygame.draw.polygon(surface, RED, [back_left, flame_tip, back_right])


def draw_text(surface, font, text, pos, color=WHITE):
    surface.blit(font.render(text, True, color), pos)


def draw_ufo(surface, ufo):
    body = pygame.Rect(0, 0, ufo.radius * 2.4, ufo.radius * 1.1)
    body.center = (ufo.pos.x, ufo.pos.y)
    dome = pygame.Rect(0, 0, ufo.radius * 1.3, ufo.radius * 1.1)
    dome.center = (ufo.pos.x, ufo.pos.y - ufo.radius * 0.5)
    pygame.draw.ellipse(surface, WHITE, body, width=2)
    pygame.draw.ellipse(surface, WHITE, dome, width=2)
    pygame.draw.line(surface, WHITE, (body.left, body.centery), (body.right, body.centery), 2)


def main():
    try:
        pygame.mixer.pre_init(frequency=sound.SAMPLE_RATE, size=-16, channels=2, buffer=512)
    except pygame.error:
        pass

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Asteroids")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 24)
    big_font = pygame.font.SysFont("consolas", 48)

    try:
        sounds = sound.Sounds()
        thrust_channel = pygame.mixer.Channel(0)
        ufo_channel = pygame.mixer.Channel(1)
    except pygame.error:
        # No audio device available (e.g. headless environment) - play silently.
        sounds = None
        thrust_channel = None
        ufo_channel = None

    def play(clip):
        if sounds is not None:
            clip.play()

    ship = Ship()
    bullets = []
    asteroids = spawn_wave(4)
    particles = []
    ufo = None
    ufo_bullets = []
    ufo_spawn_timer = random.randint(*UFO_SPAWN_DELAY_RANGE)
    score = 0
    lives = 3
    game_over = False
    respawn_timer = 0

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and ship.alive and ship.can_shoot():
                    bullets.append(ship.shoot())
                    play(sounds.shoot)
                if event.key == pygame.K_r and game_over:
                    ship = Ship()
                    bullets = []
                    asteroids = spawn_wave(4)
                    particles = []
                    ufo = None
                    ufo_bullets = []
                    ufo_spawn_timer = random.randint(*UFO_SPAWN_DELAY_RANGE)
                    score = 0
                    lives = 3
                    game_over = False
                    respawn_timer = 0
                    if thrust_channel is not None:
                        thrust_channel.stop()
                    if ufo_channel is not None:
                        ufo_channel.stop()
                if event.key == pygame.K_ESCAPE:
                    running = False

        keys = pygame.key.get_pressed()
        thrusting = False

        if not game_over:
            if ship.alive:
                thrusting = ship.update(keys)
            elif respawn_timer > 0:
                respawn_timer -= 1
                if respawn_timer == 0:
                    ship = Ship()

            if thrust_channel is not None:
                if thrusting and not thrust_channel.get_busy():
                    thrust_channel.play(sounds.thrust, loops=-1)
                elif not thrusting and thrust_channel.get_busy():
                    thrust_channel.stop()

            for bullet in bullets:
                bullet.update()
            bullets = [b for b in bullets if not b.is_dead()]

            for asteroid in asteroids:
                asteroid.update()

            for particle in particles:
                particle.update()
            particles = [p for p in particles if not p.is_dead()]

            # Flying saucer: spawn occasionally, fly across, and shoot at the ship.
            if ufo is None:
                ufo_spawn_timer -= 1
                if ufo_spawn_timer <= 0:
                    ufo = UFO()
                    if ufo_channel is not None:
                        ufo_channel.play(sounds.ufo_hum, loops=-1)
            else:
                ufo.update()
                if ufo.offscreen():
                    ufo = None
                    ufo_spawn_timer = random.randint(*UFO_SPAWN_DELAY_RANGE)
                    if ufo_channel is not None:
                        ufo_channel.stop()
                elif ship.alive and ufo.can_shoot():
                    ufo_bullets.append(ufo.shoot(ship.pos))
                    play(sounds.ufo_shoot)

            for bullet in ufo_bullets:
                bullet.update()
            ufo_bullets = [b for b in ufo_bullets if not b.is_dead()]

            # Bullet vs asteroid collisions
            surviving_asteroids = []
            for asteroid in asteroids:
                hit_bullet = None
                for bullet in bullets:
                    if distance(bullet.pos, asteroid.pos) < asteroid.radius:
                        hit_bullet = bullet
                        break
                if hit_bullet:
                    bullets.remove(hit_bullet)
                    score += ASTEROID_SCORES[asteroid.size]
                    particles.extend(spawn_explosion(
                        asteroid.pos, count=14, speed_range=(0.5, 3.5), lifetime_range=(15, 30),
                    ))
                    play(sounds.asteroid_explosion)
                    surviving_asteroids.extend(asteroid.split())
                else:
                    surviving_asteroids.append(asteroid)
            asteroids = surviving_asteroids

            # Bullet vs UFO collisions
            if ufo is not None:
                hit_bullet = next((b for b in bullets if distance(b.pos, ufo.pos) < ufo.radius), None)
                if hit_bullet:
                    bullets.remove(hit_bullet)
                    score += UFO_SCORE
                    particles.extend(spawn_explosion(
                        ufo.pos, count=20, speed_range=(0.5, 4), lifetime_range=(20, 40),
                    ))
                    play(sounds.asteroid_explosion)
                    ufo = None
                    ufo_spawn_timer = random.randint(*UFO_SPAWN_DELAY_RANGE)
                    if ufo_channel is not None:
                        ufo_channel.stop()

            def kill_ship():
                nonlocal lives, respawn_timer, game_over
                ship.alive = False
                lives -= 1
                respawn_timer = FPS
                particles.extend(spawn_explosion(
                    ship.pos, count=35, speed_range=(1, 6), lifetime_range=(25, 55), color=RED,
                ))
                particles.extend(spawn_explosion(
                    ship.pos, count=20, speed_range=(1, 4), lifetime_range=(20, 40), color=WHITE,
                ))
                play(sounds.ship_explosion)
                if thrust_channel is not None:
                    thrust_channel.stop()
                if lives <= 0:
                    game_over = True

            # Ship vs asteroid collisions
            if ship.alive:
                for asteroid in asteroids:
                    if distance(ship.pos, asteroid.pos) < asteroid.radius + ship.radius * 0.6:
                        kill_ship()
                        break

            # Ship vs UFO bullet collisions
            if ship.alive:
                hit_bullet = next(
                    (b for b in ufo_bullets if distance(ship.pos, b.pos) < ship.radius + 3), None
                )
                if hit_bullet:
                    ufo_bullets.remove(hit_bullet)
                    kill_ship()

            # Ship vs UFO collisions
            if ship.alive and ufo is not None and distance(ship.pos, ufo.pos) < ufo.radius + ship.radius * 0.6:
                kill_ship()

            if not asteroids:
                asteroids = spawn_wave(min(4 + score // 500, 8))

        screen.fill(BLACK)

        for asteroid in asteroids:
            pygame.draw.polygon(screen, WHITE, asteroid.points(), width=2)

        for bullet in bullets:
            pygame.draw.circle(screen, bullet.color, bullet.pos, 2)

        for bullet in ufo_bullets:
            pygame.draw.circle(screen, bullet.color, bullet.pos, 2)

        if ufo is not None:
            draw_ufo(screen, ufo)

        for particle in particles:
            particle.draw(screen)

        if ship.alive:
            draw_ship(screen, ship, thrusting)

        draw_text(screen, font, f"Score: {score}", (10, 10))
        draw_text(screen, font, f"Lives: {lives}", (10, 36))

        if game_over:
            draw_text(screen, big_font, "GAME OVER", (WIDTH / 2 - 140, HEIGHT / 2 - 40))
            draw_text(screen, font, "Press R to restart", (WIDTH / 2 - 90, HEIGHT / 2 + 20))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
