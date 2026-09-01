import pygame

pygame.init()

# Screen setup
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Physics Simulator")

clock = pygame.time.Clock()

# Circle properties
pos = pygame.Vector2(WIDTH//2, HEIGHT//2)
vel = pygame.Vector2(0, 0)
acc = pygame.Vector2(0, 0)
radius = 30
damping = 0.98  # simulates slippery surface

dragging = False
mouse_start = pygame.Vector2(0, 0)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Start dragging if mouse clicks on circle
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.Vector2(event.pos)
            if (mouse_pos - pos).length() <= radius:
                dragging = True
                mouse_start = mouse_pos

        # On release, set acceleration based on drag
        if event.type == pygame.MOUSEBUTTONUP and dragging:
            mouse_end = pygame.Vector2(event.pos)
            acc = (mouse_end - mouse_start) * 0.1  # scale to adjust strength
            dragging = False

    # Physics update
    vel += acc
    pos += vel
    vel *= damping
    acc *= 0  # reset acceleration

    # Keep circle on screen
    if pos.x - radius < 0 or pos.x + radius > WIDTH:
        vel.x *= -0.8  # bounce with damping
        pos.x = max(radius, min(WIDTH - radius, pos.x))
    if pos.y - radius < 0 or pos.y + radius > HEIGHT:
        vel.y *= -0.8
        pos.y = max(radius, min(HEIGHT - radius, pos.y))

    # Drawing
    screen.fill((255, 255, 255))
    pygame.draw.circle(screen, (255, 0, 0), pos, radius)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
