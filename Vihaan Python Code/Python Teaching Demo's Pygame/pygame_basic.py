import pygame

pygame.init()
screen = pygame.display.set_mode((700, 500))
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill((220, 30, 30))
    pygame.draw.rect(screen, (60, 60, 255), (20, 20, 660, 460))
    pygame.display.flip()

pygame.quit()
