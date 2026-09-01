import pygame
from pygame.math import Vector2
import sys
import os
import random
import math

# --- setup ---
pygame.init()
pygame.font.init()
font = pygame.font.SysFont('Arial', 15)

WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# colors
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (80, 200, 120)
RED = (220, 50, 50)

# plane (Airbus A320)
mass = 73500                # kg
PLANE_L = 37.6              # m
PLANE_H = 11.8              # m
MAX_THRUST = 240000         # N
THRUST_STEP = 2000          # N per frame
thrust = 0
body_angle = 45             # degrees, nose up

# world
zoom = 4                    # pixels per meter
margin = 100                # pixels
GROUND_Y = 0                # m
RADIUS = PLANE_H / 2
CLOUD_W = 80                # m
CLOUD_H = 40                # m

clouds = [(Vector2(random.randint(-4000, 4000), random.randint(-3000, -100)), random.randint(0, 3)) for _ in range(1000)]
pos = Vector2(0, -RADIUS)
cam_pos = Vector2(0, -50)
vel = Vector2(0, 0)
acc = Vector2(0, 0)
playback_speed = 0.1
dt = playback_speed*0.01  # seconds

force_gravity = Vector2(0, 9.81*mass)
MOVE_ACC = 80

plane_img = pygame.image.load("character.png")
plane_img = pygame.transform.smoothscale(plane_img, (int(PLANE_L*zoom), int(PLANE_H*zoom)))

cloud0_img = pygame.image.load("cloud0.png")
cloud0_img = pygame.transform.smoothscale(cloud0_img, (int(CLOUD_W*zoom), int(CLOUD_H*zoom)))

cloud1_img = pygame.image.load("cloud1.png")
cloud1_img = pygame.transform.smoothscale(cloud1_img, (int(CLOUD_W*zoom), int(CLOUD_H*zoom)))

cloud2_img = pygame.image.load("cloud2.png")
cloud2_img = pygame.transform.smoothscale(cloud2_img, (int(CLOUD_W*zoom), int(CLOUD_H*zoom)))

cloud3_img = pygame.image.load("cloud3.png")
cloud3_img = pygame.transform.smoothscale(cloud3_img, (int(CLOUD_W*zoom), int(CLOUD_H*zoom)))

cloud_imgs = [cloud0_img, cloud1_img, cloud2_img, cloud3_img]

def draw_2D_vector(vector, x, y, scalingFactor, input_text):
    drawVector = vector*scalingFactor
    pygame.draw.circle(screen, (150, 150, 150), (x, y), 40)
    pygame.draw.line(screen, (255,0,0), (x,y), (x+drawVector.x, y+drawVector.y), width=2)
    pygame.draw.line(screen, (0,0,255), (x,y), (x+drawVector.x, y), width=1)
    pygame.draw.line(screen, (0,0,255), (x,y), (x, y+drawVector.y), width=1)
    text_surface = font.render(input_text, True, (0, 0, 0))
    screen.blit(text_surface, (x-10,y-40))

running = True
while running:
    # --- events ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- input ---
    keys = pygame.key.get_pressed()
    acc = Vector2(0, 0)

    if keys[pygame.K_RIGHT]:
        thrust = min(thrust + THRUST_STEP, MAX_THRUST)
    if keys[pygame.K_LEFT]:
        thrust = max(thrust - THRUST_STEP, 0)
    if keys[pygame.K_UP]:
        acc.y -= MOVE_ACC
    if keys[pygame.K_DOWN]:
        acc.y += MOVE_ACC

    # calculate normal force
    if pos.y + RADIUS > GROUND_Y:
        pos.y = GROUND_Y - RADIUS
        vel.y = vel.y*-0.2
        normal_force = Vector2(0, -mass*9.81)
    elif pos.y + RADIUS < GROUND_Y:
        normal_force = Vector2(0, 0)

    # calculate some different forces
    if (vel.x != 0 and pos.y + RADIUS > GROUND_Y - 5):
        force_ground_friction = Vector2(-(vel.x/abs(vel.x))*(0.9*normal_force.magnitude()), 0)
    else:
        force_ground_friction = Vector2(0, 0)

    # thrust acts along the body angle
    force_thrust = Vector2(math.cos(math.radians(body_angle)),
                           -math.sin(math.radians(body_angle))) * thrust

    # add up all forces
    netForce = force_gravity + force_ground_friction + normal_force + force_thrust

    if netForce.magnitude() < 0.05:
        netForce = Vector2(0,0)

    # gravity
    acc += netForce/mass

    # --- physics integration ---
    vel += acc * dt
    pos += vel * dt

    # camera pans only when the player passes the margin
    sx = (pos.x - cam_pos.x) * zoom + WIDTH / 2
    sy = (pos.y - cam_pos.y) * zoom + HEIGHT / 2

    if sx > WIDTH - margin:
        cam_pos.x += (sx - (WIDTH - margin)) / zoom
    if sx < margin:
        cam_pos.x += (sx - margin) / zoom
    if sy > HEIGHT - margin:
        cam_pos.y += (sy - (HEIGHT - margin)) / zoom
    if sy < margin:
        cam_pos.y += (sy - margin) / zoom

    # --- drawing ---
    screen.fill(SKY_BLUE)

    # ground
    ground_sy = (GROUND_Y - cam_pos.y) * zoom + HEIGHT / 2
    pygame.draw.rect(screen, GRASS_GREEN, (0, ground_sy, WIDTH, HEIGHT))

    # margin border
    pygame.draw.rect(screen, RED, (margin, margin, WIDTH - 2*margin, HEIGHT - 2*margin), width=2)

    # clouds
    for cloud, randnum in clouds:
        cloudCenter = (
            (cloud.x - cam_pos.x) * zoom + WIDTH / 2,
            (cloud.y - cam_pos.y) * zoom + HEIGHT / 2
        )
        img_rect = cloud_imgs[randnum].get_rect(center=cloudCenter)
        screen.blit(cloud_imgs[randnum], img_rect)

    # player
    rot_img = pygame.transform.rotate(plane_img, body_angle)
    img_rect = rot_img.get_rect(center=(
        (pos.x - cam_pos.x) * zoom + WIDTH / 2,
        (pos.y - cam_pos.y) * zoom + HEIGHT / 2
    ))
    screen.blit(rot_img, img_rect)

    draw_2D_vector(acc, 50, 50, 0.2, 'acc')
    draw_2D_vector(netForce, 50, 150, 0.002, 'force')
    draw_2D_vector(vel, 50, 250, 0.2, 'vel')

    # throttle gauge
    throttle = thrust / MAX_THRUST * 100
    pygame.draw.rect(screen, (150, 150, 150), (30, 320, 40, 80))
    pygame.draw.rect(screen, (255, 0, 0), (30, 400 - throttle*0.8, 40, throttle*0.8))
    screen.blit(font.render(f'{throttle:.0f}%', True, (0, 0, 0)), (30, 405))

    pygame.display.flip()

pygame.quit()