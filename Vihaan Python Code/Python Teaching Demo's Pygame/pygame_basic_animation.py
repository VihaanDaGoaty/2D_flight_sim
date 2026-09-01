import pygame

pygame.init()
screen = pygame.display.set_mode((700, 500))
running = True

trail_x = []
trail_y = []

x = 20
Vx = 0.1

y = 20
Vy = 0.05

time = 0

while running:
    time += 1
    x += Vx
    y += Vy

    if (x > 670):
        Vx *= -1

    if (y > 470):
        Vy *= -1

    if (x < 0):
        Vx *= -1

    if (y < 0):
        Vy *= -1

    if (time%100 == 0):
        trail_x.append(x)
        trail_y.append(y)

        if (len(trail_x) > 150):
            trail_x.pop(0)
            trail_y.pop(0)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill((30, 30, 30))
    pygame.draw.rect(screen, (200, 200, 200), (x, y, 30, 30))
    for i in range(len(trail_x)):
        pygame.draw.circle(screen, (255, 255, 255), (trail_x[i], trail_y[i]), 5)
    pygame.display.flip()

pygame.quit()
