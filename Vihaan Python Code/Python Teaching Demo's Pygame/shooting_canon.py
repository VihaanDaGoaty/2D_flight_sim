import pygame
import math

pygame.init()

# Screen setup
WIDTH = 800
HEIGHT = 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cannon Simulator")

clock = pygame.time.Clock()

# Cannon parameters
angle = 45  # degrees
power = 10  # initial velocity scale
fired = False
trail = []
pos = pygame.Vector2(100, HEIGHT - 50)
vel = pygame.Vector2(0, 0)
g = 0.5  # gravity

# Button areas
fire_button = pygame.Rect(700, 400, 80, 40)
angle_slider = pygame.Rect(600, 100, 150, 20)
power_slider = pygame.Rect(600, 200, 150, 20)

def draw_slider(rect, value, max_value):
    pygame.draw.rect(screen, (180,180,180), rect)
    handle_x = rect.x + (value / max_value) * rect.width
    pygame.draw.circle(screen, (0,0,0), (int(handle_x), rect.y + rect.height//2), 10)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Mouse click events
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # Check if fire button pressed
            if fire_button.collidepoint(mx, my):
                fired = True
                vel = pygame.Vector2(math.cos(math.radians(angle)), -math.sin(math.radians(angle))) * power
                pos = pygame.Vector2(100, HEIGHT - 50)
                trail = [pos.copy()]
            # Check if sliders clicked
            if angle_slider.collidepoint(mx, my):
                dragging_angle = True
            else:
                dragging_angle = False
            if power_slider.collidepoint(mx, my):
                dragging_power = True
            else:
                dragging_power = False

        if event.type == pygame.MOUSEBUTTONUP:
            dragging_angle = dragging_power = False

    # Slider dragging
    mx, my = pygame.mouse.get_pos()
    if 'dragging_angle' in locals() and dragging_angle:
        angle = int((mx - angle_slider.x) / angle_slider.width * 90)
        angle = max(0, min(90, angle))
    if 'dragging_power' in locals() and dragging_power:
        power = int((mx - power_slider.x) / power_slider.width * 40)
        power = max(1, min(40, power))

    # Physics update if fired
    if fired:
        vel.y += g
        pos += vel
        trail.append(pos.copy())
        # Stop if it hits ground
        if pos.y >= HEIGHT - 50:
            pos.y = HEIGHT - 50
            vel = pygame.Vector2(0,0)
            fired = False

    # Drawing
    screen.fill((255,255,255))
    
    # Draw ground
    pygame.draw.rect(screen, (0,150,0), (0, HEIGHT-50, WIDTH, 50))
    
    # Draw cannon (simple rectangle)
    end_x = 100 + math.cos(math.radians(angle)) * 40
    end_y = HEIGHT-50 - math.sin(math.radians(angle)) * 40
    pygame.draw.line(screen, (0,0,0), (100, HEIGHT-50), (end_x, end_y), 5)
    
    # Draw trail
    for t in trail:
        pygame.draw.circle(screen, (255,0,0), (int(t.x), int(t.y)), 5)
    
    # Draw projectile
    if fired:
        pygame.draw.circle(screen, (0,0,255), (int(pos.x), int(pos.y)), 10)

    # Draw buttons and sliders
    pygame.draw.rect(screen, (0,0,255), fire_button)
    font = pygame.font.SysFont(None, 24)
    screen.blit(font.render("FIRE", True, (255,255,255)), (fire_button.x+10, fire_button.y+10))
    draw_slider(angle_slider, angle, 90)
    screen.blit(font.render("Angle", True, (0,0,0)), (angle_slider.x, angle_slider.y-25))
    draw_slider(power_slider, power, 20)
    screen.blit(font.render("Power", True, (0,0,0)), (power_slider.x, power_slider.y-25))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
