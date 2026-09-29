# General Dynamics F-16C Fighting Falcon
# values not yet checked against a primary source
name = "F-16C Fighting Falcon"

# geometry
size = [15.06, 5.09] #units are meters, length and height
wing_area = 27.87 #units are meters^2
aspect_ratio = 3.2 #unitless, wingspan^2 / wing area

# mass
dry_mass = 9200 #units are kg, aircraft plus payload, no fuel
fuel_mass_start = 3200 #units are kg
fuel_mass_max = 3200 #units are kg, internal fuel only
fuel_density = 0.804 #units are kg per litre, JP-8

# engines
max_thrust = 129000 #units are newtons, F110-GE-129 with afterburner
thrust_step = 800 #units are newtons per frame
tsfc = 0.0000213 #units are kg per newton per second, military power

# aerodynamics
stall_angle = 25.0 #units are degrees
c_l_angleSlope = 0.06 #units are 1/degrees
c_l_y_intercept = 0.0 #unitless, symmetric wing
c_l_stallSlope = 0.04 #units are 1/degrees, drop after stall
c_d_parasite = 0.022 #unitless, referenced to wing area
oswald_efficiency = 0.7 #unitless

# limits
load_factor_max = 9.0 #unitless, structural limit

# ground
rolling_friction = 0.03 #unitless

# published figures, for validation
takeoff_distance = 500 #units are meters, sea level
stall_speed_clean = 65 #units are meters per second

# image
image_file = "f16_img.png"