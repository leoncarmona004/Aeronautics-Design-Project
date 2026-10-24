######################################################
import sys
from pathlib import Path

for parent in Path(__file__).resolve().parents:
    if (parent / "tools").is_dir():
        sys.path.append(str(parent))
        break

from tools.unit_conversions import *
from tools.reusable_functions import *
#######################################################

import numpy as np
import matplotlib.pyplot as plt

part = "wing" #part of the code to compute

g = 9.81 #m/s^2 - acceleration due to gravity


#### INITIAL DETERMINATION OF WING CHARACTERISTICS ####

if part == "wing":

    W_TO = 3500 * 9.81 #N -  First approximation of the weight of the aircraft
    AR = 8 #aspect ratio (assumption based on slide 24 Conception Design)
    taper = 0.7 #taper ratio (assimption based on the P2012 aircraft)

    # Stall situation
    V_stall = 22 #m/s - stall speed of the aircraft (assumption based on the P2012 aircraft)
    rho_ground = 1.225 #kg/m^3 - air density at sea level
    C_L_max = 4 #maximum lift coefficient (assumption based on slide 32 Conception Design)

    # Cruise conditions
    V_cruise = kt_to_ms(250) #m/s - target cruise speed (225?)
    h_cruise = 10800 #m - cruise altitude based on a design altitude of 10.8 km (TO BE CHECKED)
    rho_cruise = 0.4 #kg/m^3 - air density at cruise altitude (assumption based on slide 7 Conception Design) (TO BE CHECKED!)
    rho_cruise = air_density(h_cruise)
    # Characteristic of the wing commputed from the stall limit
    S = (2*W_TO)/(rho_ground*(V_stall**2)*C_L_max) #m^2 - gross surface area of the wing
    b = np.sqrt(AR*S) #m - wingspan of the aircraft
    c_bar = S/b #m - mean aerodynamic chord of the wing
    c_root = (2*S)/(b*(1+taper)) #m - root chord of the wing (assuming a trapezoidal wing)
    c_tip = taper*c_root #m - tip chord of the wing
    twist_angle = np.deg2rad(-3) #rad - twist angle of the wing (assumption based on Raymer reference)

    # Computation of cruise conditions
    C_L_cruise = (2*W_TO)/(rho_cruise*(V_cruise**2)*S) #lift coefficient at cruise
            
    print(f"Wing characteristics:")
    print(f"Surface area of the wing (S): {S:.3f} m^2")
    print(f"Stall speed of the aircraft (V_stall): {V_stall} m/s")
    print(f"Aspect ratio of the wing (AR): {AR}")
    print(f"Wingspan of the aircraft (b): {b:.3f} m")
    print(f"Mean aerodynamic chord of the wing (c_bar): {c_bar:.3f} m")
    print(f"Taper ratio of the wing (taper): {taper}")
    print(f"Root chord of the wing (c_root): {c_root:.3f} m")
    print(f"Tip chord of the wing (c_tip): {c_tip:.3f} m")
    print(f"Twist angle of the wing (theta): {np.degrees(twist_angle):.0f} [deg]")
    print(f"Lift coefficient at cruise (C_L_cruise): {C_L_cruise:.3f}")


##### POWER REQUIRED FOR TAKE OFF ##### (old code)
"""
if part == "power":
    W_TO = 3500 * 9.81 #N -  First approximation of the weight of the aircraft
    rho_ground = 1.225 #kg/m^3 - air density at sea level

    # Project guidelines
    x_tot = ft_to_m(300) #m - total distance for take off 
    h_obs = ft_to_m(50) #m - obstacle height to clear during take off    

    # Data based on course slides
    mu = 0.02 #coefficient of friction (slide 49 Performance - able to land on concrete and asphalt)
    C_D0 = 0.02 #zero-lift drag coefficient (assumption based on slide 24 Performance
    e = 0.8 #Oswald efficiency factor (assumption based on slide 24 Performance)

    # Data obtained from the previous part of the code
    S = 62.286 #m^2 - gross surface area of the wing
    AR = 8 #aspect ratio

    # Speeds
    V_stall = 15 #m/s - stall speed of the aircraft (assumption based on similar STOL aircrafts)
    V_LOF = 1.1 * V_stall #m/s - lift off speed of the aircraft
    V_TR = 1.15 * V_stall #m/s - transition speed of the aircraft

    # Rotation distance
    x_R = 1*V_LOF #m - rotation distance (General Aviation Aircraft Design - Chapter 17 page 23)

    # Transition and climb distances
    n = 1.2 #load factor (assumption)
    R = V_TR**2/(g*(n-1)) #m - radius of turn (General Aviation Aircraft Design - Chapter 17 page 24)
    h_TR = h_obs #m - transition height (we take the limiting case: the obstacle has been cleared at the transition speed)
    theta = np.arccos(1 - (h_TR/R)) #rad - climb angle (General Aviation Aircraft Design - Chapter 17 page 23)
    x_TR = R * np.sin(theta) #m - transition distance (General Aviation Aircraft Design - Chapter 17 page 23)
    x_CL = (h_obs - h_TR)/np.tan(theta) #m - climb distance (General Aviation Aircraft Design - Chapter 17 page 24)

    # Ground roll distance
    x_G = x_tot - x_R - x_TR - x_CL #m - ground roll distance
    a = W_TO*V_LOF**2/(2*x_G)

    # Conditions at lift off
    L = n*W_TO #N - lift at lift off (from the load factor)
    C_L_ground = L/(0.5*rho_ground*V_LOF**2*S) #lift coefficient at lift off
    C_D_ground = C_D0 + (C_L_ground**2)/(np.pi*AR*e) #drag coefficient at lift off
    D = 0.5*rho_ground*V_LOF**2*S*C_D_ground #N - drag at lift off
    T_TO = a/g + D + mu*(W_TO - L) #N - thrust required for take off
    P_TO = T_TO * V_LOF / np.sqrt(2) #W - power required for take off
    P_TO_hp = W_to_hp(P_TO) #hp - power required for take off

    print(f"SPEEDS")
    print(f"Lift off speed of the aircraft (V_LOF): {V_LOF:.2f} m/s")
    print(f"Transition speed of the aircraft (V_TR): {V_TR:.2f} m/s")

    print(f"\nDISTANCES")
    print(f"Ground roll distance (x_G): {x_G:.2f} m = {m_to_ft(x_G):.0f} ft")
    print(f"Rotation distance (x_R): {x_R:.2f} m = {m_to_ft(x_R):.0f} ft")
    print(f"Transition distance (x_TR): {x_TR:.2f} m = {m_to_ft(x_TR):.0f} ft")
    print(f"Climb distance (x_CL): {x_CL:.2f} m = {m_to_ft(x_CL):.0f} ft")
    print(f"Total distance for take off (x_tot): {x_tot:.2f} m = {m_to_ft(x_tot):.0f} ft")

    print(f"\nTHRUST AND POWER")
    print(f"Thrust required for take off (T_TO): {T_TO:.2f} N")
    print(f"Power required for take off (P_TO): {P_TO:.2f} W = {P_TO_hp:.2f} hp")

    """