import pygame

pygame.init()

screen = pygame.display.set_mode((500, 400))
#pygame.display.set_caption("Circle Follows Mouse")

running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((255, 255, 255))  # White background
    
    mouse_x, mouse_y = pygame.mouse.get_pos()  # Get mouse position
    pygame.draw.circle(screen, (255, 0, 0), (mouse_x, mouse_y), 30)  # Draw circle
    
    pygame.display.flip()
    clock.tick(60)  # Limit to 60 FPS

pygame.quit()