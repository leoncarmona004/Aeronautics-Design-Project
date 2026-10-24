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

g = 9.81 # [m/s^2]

# Aircraft characteristics (estimates) :

m_to = 3500 # [kg]
rho_ground = 1.225 # [kg/m^3]
mu = 0.02 
# v_s = 22 # [m/s]
C_D_0 = 0.025
e = 0.755
C_L_max = 4
AR = 8
n = 1.2 # assumption to be checked!
x_target = ft_to_m(300) # [m]
h = ft_to_m(50) # [m]

# Takeoff weight
W_to = m_to * g # [N]

# Wing surface area
# S = W_to / (0.5 * rho_ground * v_s**2 * C_L_max)

S = 28.955 # [m^2] fixed wing surface area 

v_s = np.sqrt(W_to / (0.5 * rho_ground * S * C_L_max)) # [m/s]

# Liftoff speed
k_1 = 1.1
v_LOF = k_1 * v_s # [m/s]

# Lift at liftoff
L_LOF = n * W_to
C_L_LOF = L_LOF / (0.5 * rho_ground * v_LOF**2 * S)
#C_L_LOF = np.pi*e*mu*AR ??

# Drag at liftoff
C_D_LOF = C_D_0 + C_L_LOF**2 / (np.pi * e * AR)
D_LOF = 0.5 * (rho_ground * v_LOF**2 * C_D_LOF * S)

# Required takeoff thrust 
mu_prime = mu + 0.72 * (C_D_0 / C_L_max)

T_avg = 30000 # [N] (initial guess)
x_g = (v_LOF**2 / (2 * g)) / ((T_avg / W_to) - mu_prime)
max_iter = 1000
tol = 0.01

for i in range(max_iter):

    gamma_LOF = 0.9 * (T_avg/W_to) - (0.3 / np.sqrt(AR))
    x_a = v_LOF**2 / (g * np.sqrt(2)) + (h / (gamma_LOF))
    if x_a > x_target:
        print("Negative ground run")
    x_g = x_target - x_a
    T_new = W_to * (v_LOF**2 / (2 * g * x_g) + mu_prime)

    error = abs(T_new - T_avg)
    # print(f"Error : {error:.2f}")
    T_avg = T_new
    if error < tol:
        T_avg = T_new
        break

eta_prop = 0.75
P_avg = T_avg * (v_LOF / np.sqrt(2))  # use v_to or v_LOF ? 
P_shaf_avg = P_avg / eta_prop

print(f"Takeoff weight W_to = {W_to:.2f} N")
print(f"Wing surface area S = {S:.3f} m^2")
print(f"Stall speed v_s = {v_s:.2f} m/s")
print(f"Liftoff speed v_LOF = {v_LOF:.2f} m/s")
print(f"Liftoff Lift L_LOF = {L_LOF:.2f} N -> C_L_LOF = {C_L_LOF:.2f}")
print(f"Liftoff Drag D_LOF = {D_LOF:.2f} N as C_D_LOF = {C_D_LOF:.2f}")
print(f"Ground run x_g = {x_g:.2f} m or x_g = {m_to_ft(x_g):.2f} ft")
print(f"Takeoff thrust T_avg = {T_avg:.2f} N")
print(f"Takeoff power P_to = {P_avg/1000:.2f} kW or P_to = {W_to_hp(P_avg):.2f} hp")
print(f"Takeoff power to the shaft : P_to_shaft = {P_shaf_avg/1000:.2f} kW or P_to_shaft = {W_to_hp(P_shaf_avg):.2f} hp")
