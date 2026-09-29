import pygame
from pygame.math import Vector2
import sys
import os
import random
import math
import csv
import datetime

# --- setup ---
pygame.init()
pygame.font.init()
font = pygame.font.SysFont('Arial', 15)

WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
FPS = 60

# display options
show_camera_move_margin = True
show_extra_displays = True
save_raw_data = True
save_log_dt = 0.1 #seconds between logged rows

rho = 1.225 #units are kg per m^3
wing_area = 122.4 #units are meters^2, A320-100
stall_angle = 13.682 #units are degrees
c_l_angleSlope = 0.09 #units are 1/degrees
c_l_y_intercept = 0.15 #unitless
c_l_stallSlope = 0.05 #units are 1/degrees, drop after stall
c_d = 0.03 #unitless, referenced to wing area

# colors
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (80, 200, 120)
RED = (220, 50, 50)

body_angle = 0
angle_step = 1

plane_max_thrust = 222000

current_thrust = 0

thrust_step = 500

current_thrust_force = Vector2(0,0)

# physics
clouds = [(Vector2(random.randint(-1000, 20000), random.randint(-5000, HEIGHT-200)), random.randint(0, 3)) for _ in range(1000)]
cam_pos = Vector2(WIDTH / 2, HEIGHT / 2)
vel = Vector2(0, 0)
acc = Vector2(0, 0)
mass = 64000
playback_speed = 1
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

pos = Vector2(WIDTH / 2, GROUND_Y - RADIUS)
start_x = pos.x

# data logging
start_time = datetime.datetime.now()
run_data = []
sim_time = 0
next_log_time = 0

plane_src = pygame.image.load("character.png")
cloud_src = [pygame.image.load("cloud0.png"),
             pygame.image.load("cloud1.png"),
             pygame.image.load("cloud2.png"),
             pygame.image.load("cloud3.png")]

def c_l_fromAngle(a):
    c_l_peak = c_l_angleSlope * stall_angle + c_l_y_intercept
    if a > stall_angle:
        c_l = c_l_peak - c_l_stallSlope * (a - stall_angle)
        if c_l < 0:
            c_l = 0
        return c_l
    if a < -stall_angle:
        c_l = -c_l_peak - c_l_stallSlope * (a + stall_angle)
        if c_l > 0:
            c_l = 0
        return c_l
    c_l = c_l_angleSlope * a + c_l_y_intercept
    return c_l

def rescale():
    global plane_img, cloud_imgs
    plane_img = pygame.transform.smoothscale(plane_src, (plane_size[0]*zoom, plane_size[1]*zoom))
    cloud_imgs = [pygame.transform.smoothscale(c, (cloud_size[0]*zoom, cloud_size[1]*zoom)) for c in cloud_src]

rescale()

def draw_2D_vector(vector, x, y, ref_max, label, unit):
    size = 88
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
        d = vector / ref_max * (half - 5)
        if d.magnitude() > half - 5:
            d = d.normalize() * (half - 5)
        pygame.draw.line(screen, (120, 120, 255), (cx, cy), (cx+d.x, cy), width=1)
        pygame.draw.line(screen, (120, 120, 255), (cx, cy), (cx, cy+d.y), width=1)
        pygame.draw.line(screen, (200, 0, 0), (cx, cy), (cx+d.x, cy+d.y), width=2)

    # convert the printed number to readable units
    if unit == 'mph':
        mag = mag * 2.23694
    if unit == 'kN':
        mag = mag / 1000

    screen.blit(font.render(label, True, (0, 0, 0)), (x, y - 16))
    screen.blit(font.render(f'{mag:.0f} {unit}', True, (60, 60, 60)), (x, y + size + 2))

def draw_wing(x, y, body_a, flight_a):
    pygame.draw.rect(screen, (235, 235, 235), (x, y, 160, 100))
    pygame.draw.rect(screen, (90, 90, 90), (x, y, 160, 100), width=1)
    cx = x + 80
    cy = y + 50

    # oncoming air, always right to left
    for ay in (cy - 30, cy, cy + 30):
        pygame.draw.line(screen, (120, 120, 255), (x + 150, ay), (x + 10, ay), width=1)
        pygame.draw.line(screen, (120, 120, 255), (x + 10, ay), (x + 18, ay - 4), width=1)
        pygame.draw.line(screen, (120, 120, 255), (x + 10, ay), (x + 18, ay + 4), width=1)

    # wing, tilted by angle of attack
    br = math.radians(body_a - flight_a)
    dx = 35 * math.cos(br)
    dy = -35 * math.sin(br)
    pygame.draw.line(screen, (0, 0, 0), (cx - dx, cy - dy), (cx + dx, cy + dy), width=5)

    screen.blit(font.render('wing', True, (0, 0, 0)), (x, y - 16))
    screen.blit(font.render(f'AoA {body_a - flight_a:.1f} deg', True, (60, 60, 60)), (x, y + 102))

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

    # ground contact
    if pos.y + RADIUS >= GROUND_Y:
        pos.y = GROUND_Y - RADIUS
        if vel.y > 0:
            vel.y = 0
        on_ground = True
    else:
        on_ground = False

    # thrust acts along the body angle
    current_thrust_force = Vector2(math.cos(math.radians(body_angle)),
                                   -math.sin(math.radians(body_angle))) * current_thrust

    # angle of attack
    if vel.magnitude() > 1:
        flight_angle = -math.degrees(math.atan2(vel.y, vel.x))
    else:
        flight_angle = 0
    aoa = body_angle - flight_angle
    c_l = c_l_fromAngle(aoa)

    # lift, perpendicular to velocity
    if vel.magnitude() > 1:
        lift_mag = 0.5 * c_l * rho * vel.magnitude()**2 * wing_area
        force_lift = Vector2(vel.y, -vel.x).normalize() * lift_mag
    else:
        force_lift = Vector2(0, 0)

    # drag, opposite to velocity
    if vel.magnitude() > 1:
        drag_mag = 0.5 * c_d * rho * vel.magnitude()**2 * wing_area
        force_drag = -vel.normalize() * drag_mag
    else:
        force_drag = Vector2(0, 0)

    # normal force cancels whatever downward force is left
    if on_ground:
        other_y = force_gravity.y + current_thrust_force.y + force_lift.y + force_drag.y
        if other_y > 0:
            normal_force = Vector2(0, -other_y)
        else:
            normal_force = Vector2(0, 0)
            on_ground = False
    else:
        normal_force = Vector2(0, 0)

    # friction opposes rolling, scaled by how much weight is on the wheels
    if on_ground and vel.x != 0:
        force_ground_friction = Vector2(-(vel.x/abs(vel.x))*(0.03*normal_force.magnitude()), 0)
    else:
        force_ground_friction = Vector2(0, 0)

    # add up all forces
    netForce = force_gravity + force_ground_friction + normal_force + current_thrust_force + force_lift + force_drag

    if netForce.magnitude() < 0.05:
        netForce = Vector2(0,0)

    # gravity
    acc += netForce/mass

    # --- physics integration ---
    vel += acc * dt
    pos += vel * dt
    sim_time += dt

    # --- data logging ---
    altitude = GROUND_Y - (pos.y + RADIUS)
    x_disp = pos.x - start_x
    if save_raw_data and sim_time >= next_log_time:
        next_log_time += save_log_dt
        run_data.append([
            round(sim_time, 4),
            round(pos.x, 3), round(pos.y, 3),
            round(x_disp, 3), round(altitude, 3),
            round(vel.x, 3), round(vel.y, 3), round(vel.magnitude(), 3),
            round(acc.x, 3), round(acc.y, 3),
            round(body_angle, 2), round(flight_angle, 2), round(aoa, 2),
            round(c_l, 4),
            round(current_thrust, 1),
            round(current_thrust_force.x, 1), round(current_thrust_force.y, 1),
            round(force_lift.x, 1), round(force_lift.y, 1),
            round(force_drag.x, 1), round(force_drag.y, 1),
            round(force_ground_friction.x, 1),
            round(normal_force.y, 1),
            round(netForce.x, 1), round(netForce.y, 1),
            int(on_ground), int(abs(aoa) > stall_angle)
        ])

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
    if show_camera_move_margin:
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

    # velocity direction on the plane
    if vel.magnitude() > 1:
        px = (pos.x - cam_pos.x) * zoom + WIDTH / 2
        py = (pos.y - cam_pos.y) * zoom + HEIGHT / 2
        vdir = vel.normalize() * 60
        pygame.draw.line(screen, (0, 0, 255), (px, py), (px + vdir.x, py + vdir.y), width=2)

    if show_extra_displays:
        draw_2D_vector(acc,      30,  40, 20,     'acc',   'm/s²')
        draw_2D_vector(vel,      30, 168, 150,    'vel',   'mph')
        draw_2D_vector(netForce, 30, 296, 700000, 'force', 'kN')

        # throttle gauge
        throttle = current_thrust / plane_max_thrust * 100
        pygame.draw.rect(screen, (235, 235, 235), (30, 426, 30, 88))
        pygame.draw.rect(screen, (200, 0, 0), (30, 514 - throttle*0.88, 30, throttle*0.88))
        pygame.draw.rect(screen, (90, 90, 90), (30, 426, 30, 88), width=1)
        screen.blit(font.render('throttle', True, (0, 0, 0)), (30, 410))
        screen.blit(font.render(f'{throttle:.0f} %', True, (60, 60, 60)), (30, 516))

        # readouts
        if abs(altitude) >= 1000:
            screen.blit(font.render(f'altitude   {altitude/1000:8.2f} km', True, (0, 0, 0)), (30, 546))
        else:
            screen.blit(font.render(f'altitude   {altitude:8.1f} m', True, (0, 0, 0)), (30, 546))

        if abs(x_disp) >= 1000:
            screen.blit(font.render(f'x-disp     {x_disp/1000:8.2f} km', True, (0, 0, 0)), (30, 564))
        else:
            screen.blit(font.render(f'x-disp     {x_disp:8.1f} m', True, (0, 0, 0)), (30, 564))

        screen.blit(font.render(f'lift coeff {c_l:8.2f}', True, (0, 0, 0)), (30, 582))
        if abs(aoa) > stall_angle:
            screen.blit(font.render('STALL', True, (200, 0, 0)), (30, 600))
        if on_ground:
            screen.blit(font.render('GROUNDED', True, (200, 0, 0)), (30, 618))

        # wing diagram
        draw_wing(WIDTH - 190, 30, body_angle, flight_angle)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()

# --- write run data ---
if save_raw_data and run_data:
    filename = f"flightsim_{start_time.strftime('%Y-%m-%d_%H-%M')}_{int(sim_time)}sec.csv"
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time_s', 'pos_x_m', 'pos_y_m', 'x_disp_m', 'altitude_m',
                         'vel_x_ms', 'vel_y_ms', 'speed_ms',
                         'acc_x_ms2', 'acc_y_ms2',
                         'body_angle_deg', 'flight_angle_deg', 'aoa_deg',
                         'c_l',
                         'thrust_N', 'thrust_x_N', 'thrust_y_N',
                         'lift_x_N', 'lift_y_N',
                         'drag_x_N', 'drag_y_N',
                         'friction_x_N', 'normal_y_N',
                         'netforce_x_N', 'netforce_y_N',
                         'on_ground', 'stalled'])
        writer.writerows(run_data)
    print(f"saved {len(run_data)} rows to {filename}")