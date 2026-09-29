# Cessna 172S Skyhawk
# values not yet checked against the Pilot's Operating Handbook
name = "Cessna 172S Skyhawk"

# geometry
size = [8.28, 2.72] #units are meters, length and height
wing_area = 16.2 #units are meters^2
aspect_ratio = 7.5 #unitless, wingspan^2 / wing area

# mass
dry_mass = 890 #units are kg, aircraft plus payload, no fuel
fuel_mass_start = 100 #units are kg
fuel_mass_max = 144 #units are kg, 200 L of avgas
fuel_density = 0.72 #units are kg per litre, avgas 100LL

# engines
max_thrust = 2400 #units are newtons, static thrust, 180 hp
thrust_step = 10 #units are newtons per frame
tsfc = 0.0000215 #units are kg per newton per second

# aerodynamics
stall_angle = 16.0 #units are degrees
c_l_angleSlope = 0.1 #units are 1/degrees
c_l_y_intercept = 0.25 #unitless
c_l_stallSlope = 0.06 #units are 1/degrees, drop after stall
c_d_parasite = 0.035 #unitless, referenced to wing area
oswald_efficiency = 0.75 #unitless

# limits
load_factor_max = 3.8 #unitless, utility category

# ground
rolling_friction = 0.04 #unitless

# published figures, for validation
takeoff_distance = 290 #units are meters, sea level
stall_speed_clean = 26 #units are meters per second

# image
image_file = "c172_img.png"