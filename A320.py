# Airbus A320-100
name = "Airbus A320-100"

# geometry
size = [37.6, 11.8] #units are meters, length and height
wing_area = 122.4 #units are meters^2
aspect_ratio = 9.4 #unitless, wingspan^2 / wing area

# mass
dry_mass = 50000 #units are kg, aircraft plus payload, no fuel
fuel_mass_start = 14000 #units are kg
fuel_mass_max = 21870 #units are kg, 27200 L of Jet A-1
fuel_density = 0.804 #units are kg per litre, Jet A-1

# engines
max_thrust = 222000 #units are newtons, 2 x 111 kN
thrust_step = 500 #units are newtons per frame
tsfc = 0.000017 #units are kg per newton per second

# aerodynamics
stall_angle = 13.682 #units are degrees
c_l_angleSlope = 0.09 #units are 1/degrees
c_l_y_intercept = 0.15 #unitless
c_l_stallSlope = 0.05 #units are 1/degrees, drop after stall
c_d_parasite = 0.03 #unitless, referenced to wing area
oswald_efficiency = 0.8 #unitless

# limits
load_factor_max = 2.5 #unitless, structural limit

# ground
rolling_friction = 0.03 #unitless

# published figures, for validation
takeoff_distance = 2010 #units are meters, sea level
stall_speed_clean = 79 #units are meters per second

# image
image_file = "a320_img.png"