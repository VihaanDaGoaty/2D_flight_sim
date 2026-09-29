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
FPS = 60
rho = 1.225 #units are kg per m^3
wing_area = 122.4 #units are meters^3
stall_angle = 13.682 #units are degrees
c_l_angleSlope = 0.09 #units are 1/degrees
c_l_y_intercept = 0.15 #unitless

# colors
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (80, 200, 120)
RED = (220, 50, 50)

body_angle = 45
angle_step = 1

plane_max_thrust = 100000

current_thrust = 0

thrust_step = 100

current_thrust_force = Vector2(0,0)

# physics
clouds = [(Vector2(random.randint(-1000, 20000), random.randint(-5000, HEIGHT-200)), random.randint(0, 3)) for _ in range(1000)]
pos = Vector2(WIDTH / 2, HEIGHT / 2)
cam_pos = Vector2(WIDTH / 2, HEIGHT / 2)
start_x = pos.x
vel = Vector2(0, 0)
acc = Vector2(0, 0)
mass = 64000
playback_speed = 0.1
dt = playback_speed / FPS  # seconds
zoom = 2
zoom_min = 0.25
zoom_max = 8
margin = 100
plane_size = [37.6, 11.8]
cloud_size = [100, 50]

force_gravity = Vector2(0, 9.81*mass)
MOVE_ACC = 80
GROUND_Y = HEIGHT * 0.75
RADIUS = plane_size[1] / 2

plane_src = pygame.image.load("character.png")
cloud_src = [pygame.image.load("cloud0.png"),
             pygame.image.load("cloud1.png"),
             pygame.image.load("cloud2.png"),
             pygame.image.load("cloud3.png")]

def c_l_fromAngle(a):
    c_l = c_l_angleSlope * a + c_l_y_intercept 
    return c_l

def rescale():
    global plane_img, cloud_imgs
    plane_img = pygame.transform.smoothscale(plane_src, (plane_size[0]*zoom, plane_size[1]*zoom))
    cloud_imgs = [pygame.transform.smoothscale(c, (cloud_size[0]*zoom, cloud_size[1]*zoom)) for c in cloud_src]

rescale()

def draw_2D_vector(vector, x, y, ref_max, label, unit):
    size = 70
    half = size / 2
    cx, cy = x + half, y + half

    # frame
    pygame.draw.rect(screen, (235, 235, 235), (x, y, size, size))
    pygame.draw.rect(screen, (90, 90, 90), (x, y, size, size), width=1)
    pygame.draw.line(screen, (200, 200, 200), (x, cy), (x+size, cy), width=1)
    pygame.draw.line(screen, (200, 200, 200), (cx, y), (cx, y+size), width=1)

    # arrow, scaled so ref_max fills the box
    mag = vector.magnitude()
    if mag > 0:
        d = vector / ref_max * (half - 4)
        if d.magnitude() > half - 4:
            d = d.normalize() * (half - 4)
        pygame.draw.line(screen, (120, 120, 255), (cx, cy), (cx+d.x, cy), width=1)
        pygame.draw.line(screen, (120, 120, 255), (cx, cy), (cx, cy+d.y), width=1)
        pygame.draw.line(screen, (200, 0, 0), (cx, cy), (cx+d.x, cy+d.y), width=2)

    screen.blit(font.render(label, True, (0, 0, 0)), (x, y - 16))
    screen.blit(font.render(f'{mag:.0f} {unit}', True, (60, 60, 60)), (x, y + size + 2))

running = True
while running:
    # --- events ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEWHEEL:
            # keep the plane where it is on screen while zooming
            sx_old = (pos.x - cam_pos.x) * zoom + WIDTH / 2
            sy_old = (pos.y - cam_pos.y) * zoom + HEIGHT / 2
            zoom = min(max(zoom * (1.1 ** event.y), zoom_min), zoom_max)
            cam_pos.x = pos.x - (sx_old - WIDTH / 2) / zoom
            cam_pos.y = pos.y - (sy_old - HEIGHT / 2) / zoom
            rescale()

    # --- input ---
    keys = pygame.key.get_pressed()
    acc = Vector2(0, 0)

    if keys[pygame.K_LEFT]:
        current_thrust = max(current_thrust - thrust_step, 0)
    if keys[pygame.K_RIGHT]:
        current_thrust = min(current_thrust + thrust_step, plane_max_thrust)
    if keys[pygame.K_UP]:
        body_angle += angle_step
    if keys[pygame.K_DOWN]:
        body_angle -= angle_step

    # calculate normal force
    if pos.y + RADIUS > GROUND_Y:
        pos.y = GROUND_Y - RADIUS
        vel.y = vel.y*-0.2
        normal_force = Vector2(0, -mass*9.81)
    else:
        normal_force = Vector2(0, 0)

    # calculate some different forces
    if (vel.x != 0 and pos.y + RADIUS > GROUND_Y - 5):
        force_ground_friction = Vector2(-(vel.x/abs(vel.x))*(0.03*normal_force.magnitude()), 0)
    else:
        force_ground_friction = Vector2(0, 0)

    # thrust acts along the body angle
    current_thrust_force = Vector2(math.cos(math.radians(body_angle)),
                                   -math.sin(math.radians(body_angle))) * current_thrust

    # add up all forces
    netForce = force_gravity + force_ground_friction + normal_force + current_thrust_force

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

    draw_2D_vector(acc,      30,  40, 20,     'acc',   'm/s²')
    draw_2D_vector(vel,      30, 150, 300,    'vel',   'm/s')
    draw_2D_vector(netForce, 30, 260, 700000, 'force', 'N')

    # throttle gauge
    throttle = current_thrust / plane_max_thrust * 100
    pygame.draw.rect(screen, (235, 235, 235), (30, 390, 70, 70))
    pygame.draw.rect(screen, (200, 0, 0), (30, 460 - throttle*0.7, 70, throttle*0.7))
    pygame.draw.rect(screen, (90, 90, 90), (30, 390, 70, 70), width=1)
    screen.blit(font.render('throttle', True, (0, 0, 0)), (30, 374))
    screen.blit(font.render(f'{throttle:.0f} %', True, (60, 60, 60)), (30, 462))

    # readouts
    altitude = GROUND_Y - (pos.y + RADIUS)
    x_disp = pos.x - start_x
    screen.blit(font.render(f'altitude   {altitude:8.1f} m', True, (0, 0, 0)), (30, 500))
    screen.blit(font.render(f'x-disp     {x_disp:8.1f} m',   True, (0, 0, 0)), (30, 518))
    screen.blit(font.render(f'lift coeff {c_l_fromAngle(body_angle):8.2f}', True, (0, 0, 0)), (30, 536))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()