import pygame
from pygame.math import Vector2
import sys
import os
import random
import math
import csv
import datetime

import F16 as plane

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

# international standard atmosphere, troposphere
rho_sea_level = 1.225 #units are kg per m^3
temp_sea_level = 288.15 #units are kelvin
lapse_rate = 0.0065 #units are kelvin per meter
rho_exponent = 4.2561 #unitless

# colors
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (80, 200, 120)
RED = (220, 50, 50)

body_pitch = 0 #units are degrees, nose up positive
pitch_step = 1

current_thrust = 0
current_thrust_force = Vector2(0,0)

fuel_mass = plane.fuel_mass_start
mass = plane.dry_mass + fuel_mass

# physics
clouds = [(Vector2(random.randint(-1000, 20000), random.randint(-5000, HEIGHT-200)), random.randint(0, 3)) for _ in range(1000)]
cam_pos = Vector2(WIDTH / 2, HEIGHT / 2)
vel = Vector2(0, 0)
acc = Vector2(0, 0)
playback_speed = 1
dt = playback_speed / FPS  # seconds
zoom = 2
zoom_min = 0.25
zoom_max = 8
margin = 100
cloud_size = [100, 50]

GROUND_Y = HEIGHT * 0.75
RADIUS = plane.size[1] / 2

pos = Vector2(WIDTH / 2, GROUND_Y - RADIUS)
start_x = pos.x

# gauge ranges, scaled to the aircraft
acc_ref = 7
vel_ref = 150
force_ref = plane.dry_mass * 9.81 * 0.4

# data logging
start_time = datetime.datetime.now()
run_data = []
sim_time = 0
next_log_time = 0

plane_src = pygame.image.load(plane.image_file)
cloud_src = [pygame.image.load("cloud0.png"),
             pygame.image.load("cloud1.png"),
             pygame.image.load("cloud2.png"),
             pygame.image.load("cloud3.png")]

def c_l_fromAngle(a):
    c_l_peak = plane.c_l_angleSlope * plane.stall_angle + plane.c_l_y_intercept
    if a > plane.stall_angle:
        c_l = c_l_peak - plane.c_l_stallSlope * (a - plane.stall_angle)
        if c_l < 0:
            c_l = 0
        return c_l
    if a < -plane.stall_angle:
        c_l = -c_l_peak - plane.c_l_stallSlope * (a + plane.stall_angle)
        if c_l > 0:
            c_l = 0
        return c_l
    c_l = plane.c_l_angleSlope * a + plane.c_l_y_intercept
    return c_l

def rescale():
    global plane_img, cloud_imgs
    plane_img = pygame.transform.smoothscale(plane_src, (plane.size[0]*zoom, plane.size[1]*zoom))
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

def draw_wing(x, y, pitch, flight_a):
    pygame.draw.rect(screen, (235, 235, 235), (x, y, 160, 90))
    pygame.draw.rect(screen, (90, 90, 90), (x, y, 160, 90), width=1)
    cx = x + 80
    cy = y + 45

    # oncoming air, always right to left
    for ay in (cy - 26, cy, cy + 26):
        pygame.draw.line(screen, (120, 120, 255), (x + 150, ay), (x + 10, ay), width=1)
        pygame.draw.line(screen, (120, 120, 255), (x + 10, ay), (x + 18, ay - 4), width=1)
        pygame.draw.line(screen, (120, 120, 255), (x + 10, ay), (x + 18, ay + 4), width=1)

    # wing, tilted by angle of attack
    wing_aoa = (pitch - flight_a + 180) % 360 - 180
    br = math.radians(wing_aoa)
    dx = 32 * math.cos(br)
    dy = -32 * math.sin(br)
    pygame.draw.line(screen, (0, 0, 0), (cx - dx, cy - dy), (cx + dx, cy + dy), width=5)

    screen.blit(font.render('wing', True, (0, 0, 0)), (x, y - 16))
    screen.blit(font.render(f'AoA {wing_aoa:.1f} deg', True, (60, 60, 60)), (x, y + 92))

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
        current_thrust = max(current_thrust - plane.thrust_step, 0)
    if keys[pygame.K_RIGHT]:
        current_thrust = min(current_thrust + plane.thrust_step, plane.max_thrust)
    if keys[pygame.K_UP]:
        body_pitch += pitch_step
    if keys[pygame.K_DOWN]:
        body_pitch -= pitch_step

    # keep pitch in -180 to 180
    body_pitch = (body_pitch + 180) % 360 - 180

    # burn fuel, mass drops
    fuel_burn_rate = plane.tsfc * current_thrust
    fuel_mass = fuel_mass - fuel_burn_rate * dt
    if fuel_mass < 0:
        fuel_mass = 0
    if fuel_mass == 0:
        current_thrust = 0
    mass = plane.dry_mass + fuel_mass
    force_gravity = Vector2(0, 9.81*mass)

    # ground contact
    if pos.y + RADIUS >= GROUND_Y:
        pos.y = GROUND_Y - RADIUS
        if vel.y > 0:
            vel.y = 0
        on_ground = True
    else:
        on_ground = False

    # atmosphere at current altitude
    altitude = GROUND_Y - (pos.y + RADIUS)
    air_temp = temp_sea_level - lapse_rate * altitude
    if air_temp < 216.65:
        air_temp = 216.65
    rho = rho_sea_level * (air_temp / temp_sea_level) ** rho_exponent
    speed_of_sound = 20.05 * math.sqrt(air_temp)

    # thrust acts along the body pitch
    current_thrust_force = Vector2(math.cos(math.radians(body_pitch)),
                                   -math.sin(math.radians(body_pitch))) * current_thrust

    # angle of attack
    if vel.magnitude() > 1:
        flight_angle = -math.degrees(math.atan2(vel.y, vel.x))
    else:
        flight_angle = 0
    aoa = (body_pitch - flight_angle + 180) % 360 - 180
    c_l = c_l_fromAngle(aoa)

    # lift, perpendicular to velocity
    if vel.magnitude() > 1:
        lift_mag = 0.5 * c_l * rho * vel.magnitude()**2 * plane.wing_area
        force_lift = Vector2(vel.y, -vel.x).normalize() * lift_mag
    else:
        force_lift = Vector2(0, 0)

    # drag, opposite to velocity
    if vel.magnitude() > 1:
        dyn_pressure = 0.5 * rho * vel.magnitude()**2 * plane.wing_area
        c_d_induced = c_l**2 / (math.pi * plane.aspect_ratio * plane.oswald_efficiency)
        f_drag_parasite = -vel.normalize() * plane.c_d_parasite * dyn_pressure
        f_drag_induced = -vel.normalize() * c_d_induced * dyn_pressure
        force_drag = f_drag_parasite + f_drag_induced
    else:
        c_d_induced = 0
        f_drag_parasite = Vector2(0, 0)
        f_drag_induced = Vector2(0, 0)
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
        force_ground_friction = Vector2(-(vel.x/abs(vel.x))*(plane.rolling_friction*normal_force.magnitude()), 0)
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
    mach = vel.magnitude() / speed_of_sound
    fuel_volume = fuel_mass / 0.804
    fuel_percent = fuel_mass / plane.fuel_mass_max * 100
    if save_raw_data and sim_time >= next_log_time:
        next_log_time += save_log_dt
        run_data.append([
            round(sim_time, 4),
            round(pos.x, 3), round(pos.y, 3),
            round(x_disp, 3), round(altitude, 3),
            round(vel.x, 3), round(vel.y, 3), round(vel.magnitude(), 3),
            round(acc.x, 3), round(acc.y, 3),
            round(body_pitch, 2), round(flight_angle, 2), round(aoa, 2),
            round(c_l, 4), round(c_d_induced, 4),
            round(rho, 4), round(air_temp, 2), round(speed_of_sound, 2), round(mach, 4),
            round(mass, 1), round(fuel_mass, 2), round(fuel_volume, 1),
            round(fuel_percent, 2), round(fuel_burn_rate, 4),
            round(current_thrust, 1),
            round(current_thrust_force.x, 1), round(current_thrust_force.y, 1),
            round(force_lift.x, 1), round(force_lift.y, 1),
            round(force_drag.x, 1), round(force_drag.y, 1),
            round(f_drag_parasite.magnitude(), 1), round(f_drag_induced.magnitude(), 1),
            round(force_ground_friction.x, 1),
            round(normal_force.y, 1),
            round(netForce.x, 1), round(netForce.y, 1),
            int(on_ground), int(abs(aoa) > plane.stall_angle)
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
    rot_img = pygame.transform.rotate(plane_img, body_pitch)
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
        # gauges, two columns
        draw_2D_vector(acc,      20,  40, acc_ref,   'acc',   'm/s²')
        draw_2D_vector(vel,     118,  40, vel_ref,   'vel',   'mph')
        draw_2D_vector(netForce, 20, 180, force_ref, 'force', 'kN')

        # throttle and fuel bars
        throttle = current_thrust / plane.max_thrust * 100
        pygame.draw.rect(screen, (235, 235, 235), (118, 180, 30, 88))
        pygame.draw.rect(screen, (200, 0, 0), (118, 268 - throttle*0.88, 30, throttle*0.88))
        pygame.draw.rect(screen, (90, 90, 90), (118, 180, 30, 88), width=1)
        pygame.draw.rect(screen, (235, 235, 235), (158, 180, 30, 88))
        pygame.draw.rect(screen, (40, 120, 200), (158, 268 - fuel_percent*0.88, 30, fuel_percent*0.88))
        pygame.draw.rect(screen, (90, 90, 90), (158, 180, 30, 88), width=1)
        screen.blit(font.render('thr', True, (0, 0, 0)), (118, 164))
        screen.blit(font.render('fuel', True, (0, 0, 0)), (158, 164))
        screen.blit(font.render(f'{throttle:.0f}%', True, (60, 60, 60)), (118, 270))
        screen.blit(font.render(f'{fuel_percent:.0f}%', True, (60, 60, 60)), (158, 270))

        # readouts
        screen.blit(font.render(plane.name, True, (0, 0, 0)), (20, 300))
        screen.blit(font.render(f'fuel     {fuel_mass:8.0f} kg', True, (0, 0, 0)), (20, 324))
        screen.blit(font.render(f'         {fuel_volume:8.0f} L', True, (0, 0, 0)), (20, 342))
        screen.blit(font.render(f'mass     {mass/1000:8.2f} t', True, (0, 0, 0)), (20, 360))

        if abs(altitude) >= 1000:
            screen.blit(font.render(f'altitude {altitude/1000:8.2f} km', True, (0, 0, 0)), (20, 384))
        else:
            screen.blit(font.render(f'altitude {altitude:8.1f} m', True, (0, 0, 0)), (20, 384))

        if abs(x_disp) >= 1000:
            screen.blit(font.render(f'x-disp   {x_disp/1000:8.2f} km', True, (0, 0, 0)), (20, 402))
        else:
            screen.blit(font.render(f'x-disp   {x_disp:8.1f} m', True, (0, 0, 0)), (20, 402))

        screen.blit(font.render(f'pitch    {body_pitch:8.0f} deg', True, (0, 0, 0)), (20, 420))
        screen.blit(font.render(f'c_l      {c_l:8.2f}', True, (0, 0, 0)), (20, 438))
        screen.blit(font.render(f'c_d ind  {c_d_induced:8.3f}', True, (0, 0, 0)), (20, 456))

        if abs(aoa) > plane.stall_angle:
            screen.blit(font.render('STALL', True, (200, 0, 0)), (20, 480))
        if on_ground:
            screen.blit(font.render('GROUNDED', True, (200, 0, 0)), (78, 480))

        # wing diagram and atmosphere, right edge
        draw_wing(WIDTH - 190, 30, body_pitch, flight_angle)

        pygame.draw.rect(screen, (235, 235, 235), (WIDTH - 190, 176, 160, 78))
        pygame.draw.rect(screen, (90, 90, 90), (WIDTH - 190, 176, 160, 78), width=1)
        screen.blit(font.render('atmosphere', True, (0, 0, 0)), (WIDTH - 190, 160))
        screen.blit(font.render(f'rho   {rho:5.3f} kg/m3', True, (60, 60, 60)), (WIDTH - 184, 180))
        screen.blit(font.render(f'temp  {air_temp - 273.15:5.1f} C', True, (60, 60, 60)), (WIDTH - 184, 198))
        screen.blit(font.render(f'sound {speed_of_sound:5.1f} m/s', True, (60, 60, 60)), (WIDTH - 184, 216))
        screen.blit(font.render(f'mach  {mach:5.3f}', True, (60, 60, 60)), (WIDTH - 184, 234))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()

# --- write run data ---
if save_raw_data and run_data:
    filename = f"flightsim_{plane.name.split()[-1]}_{start_time.strftime('%Y-%m-%d_%H-%M')}_{int(sim_time)}sec.csv"
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time_s', 'pos_x_m', 'pos_y_m', 'x_disp_m', 'altitude_m',
                         'vel_x_ms', 'vel_y_ms', 'speed_ms',
                         'acc_x_ms2', 'acc_y_ms2',
                         'body_pitch_deg', 'flight_angle_deg', 'aoa_deg',
                         'c_l', 'c_d_induced',
                         'rho_kgm3', 'air_temp_K', 'speed_of_sound_ms', 'mach',
                         'mass_kg', 'fuel_mass_kg', 'fuel_volume_L',
                         'fuel_percent', 'fuel_burn_kgs',
                         'thrust_N', 'thrust_x_N', 'thrust_y_N',
                         'lift_x_N', 'lift_y_N',
                         'drag_x_N', 'drag_y_N',
                         'drag_parasite_N', 'drag_induced_N',
                         'friction_x_N', 'normal_y_N',
                         'netforce_x_N', 'netforce_y_N',
                         'on_ground', 'stalled'])
        writer.writerows(run_data)
    print(f"saved {len(run_data)} rows to {filename}")