######################################################
import sys
from pathlib import Path

for parent in Path(__file__).resolve().parents:
    if (parent / "tools").is_dir():
        sys.path.append(str(parent))
        break

from tools.unit_conversions import *
# from tools.reusable_functions import *
#######################################################

import numpy as np
import matplotlib.pyplot as plt

g = 9.81 # [m/s^2]

def air_density(h):

    """
    Range of validity: h = [0, 11 000] m 
    """
    # ISA constants
    rho0 = 1.225      # Standard sea-level air density [kg/m^3] 
    T0 = 288.15       # Standard sea-level air temperature [K]
    L = 0.0065        # Temperature rate of change with altitude [K/m]
    R = 287.05        # Specific gas constant of air [J/(kg*K)]

    rho = rho0 * (1 - L * h / T0)**(g / (R * L) - 1) #

    return rho

# Aircraft characteristics (estimates) :
m_to = 3500 # [kg]

W_to = m_to * g

v_c_kts = 225
v_c = kt_to_ms(v_c_kts)

CD_0 = 0.025
e = 0.755
#rho_c = 0.674 # [kg/m^3] at cruise altitude 10800 m

# Altitude range
h_min = 0
h_max = 11000
h = np.linspace(h_min, h_max, 1000) # [m]
rho_c = air_density(h)

AR = 8 
S = 28.955 # [m**2]
eta_p = 0.75

C_L_c = W_to / (0.5 * rho_c * v_c**2 * S)
C_D_c = CD_0 + C_L_c**2 / (e * np.pi * AR)

T_c = 0.5 * rho_c * v_c**2 * C_D_c * S # [N]

P_c = T_c * v_c # [W] 

P_c_shaft = P_c / eta_p

# Drag polar

# Theoretical drag polar: 
# C_L = np.linspace(-1.5, 2.0, 200)
# (FOR THIS PLOT, INDEP OF ALTITUDE --> REMOVE h FROM THE PLOT BELOW!)

# In the operating range of altitudes (h = [0,10 000] m):
C_L = C_L_c

C_D = CD_0 + C_L**2 / (e * np.pi * AR)

# L/D as a function of altitude : 

L_D = C_L / C_D

########################################
#               PLOTS                  #
########################################

# Plot of the air density as a function of altitude

def density_vs_altitude():

    plt.figure(figsize=(8, 5))

    plt.plot(h/1000, rho_c, color = "green")

    plt.grid(True)
    plt.ylabel(r"Air density $\rho$ [kg/m$^3$]")
    plt.xlabel("Altitude h [km]")
    plt.title("Air density vs altitude")


# Plot shaft power as a function of altitude

def power_vs_altitude():
    plt.figure(figsize=(8, 5))

    plt.plot(h / 1000, W_to_hp(P_c_shaft), color = "orange")

    plt.grid(True)
    plt.xlabel("Altitude [km]")
    plt.ylabel("Shaft power required [hp]")
    plt.title("Cruise shaft power required vs altitude")


def drag_polar_altitude():

    """
    This plot shows the C_L and C_D required in cruise to maintain cruise equilibrium
    i.e. L = W and D = T
    """

    plt.figure(figsize=(8, 5))

    plt.scatter(
        C_D,
        C_L,
        c=h / 1000,
        cmap="viridis",
        s=15
    )

    plt.colorbar(label="Altitude [km]")

    plt.xlabel(r"Drag coefficient $C_D$")
    plt.ylabel(r"Lift coefficient $C_L$")
    plt.title("Aircraft Drag Polar vs Altitude")

    plt.grid(True)
    plt.tight_layout()


def LD_vs_CL_altitude():
    # Plot L/D as a function of CL, with altitude represented by color
    plt.figure(figsize=(8, 5))

    scatter = plt.scatter(
        C_L,
        L_D,
        c=h / 1000,
        cmap="viridis",
        s=25
    )

    plt.colorbar(scatter, label="Altitude [km]")

    plt.xlabel(r"Lift coefficient $C_L$")
    plt.ylabel(r"Lift-to-drag ratio $C_L/C_D$")
    plt.title("Cruise Aerodynamic Efficiency vs Lift Coefficient")

    plt.grid(True)
    plt.tight_layout()
    

plots = False

if plots:
    density_vs_altitude()
    power_vs_altitude()
    drag_polar_altitude()
    LD_vs_CL_altitude()

"""
# Next step: trade off study of optimal cruise altitude such that the total energy required
# required for takeoff, climb and cruise is minimised.
"""

# Chosen optimal cruise altitude
h_c = 8000 # [m] 

# Find the index corresponding to the chosen altitude
i_c = np.argmin(np.abs(h - h_c))

print(f"Cruise speed: v_c = {v_c_kts:.2f} kt or v_c = {v_c:.2f} m/s ({ms_to_kmh(v_c):.2f} km/h)")
print(f"Considered cruise altitude range: h = [{h_min:.0f},{h_max:.0f}] m")
print(f"Cruise C_L_c ranges from C_L_c(h = {h_min:.0f}) = {C_L_c[0]:.3f} to C_L_c(h = {h_max:.0f}) = {C_L_c[-1]:.3f}")
print(f"Cruise C_D_c ranges from C_D_c(h = {h_min}) = {C_D_c[0]:.3f} to C_D_c(h = {h_max:.0f}) = {C_D_c[-1]:.3f}")
print()
print(f"Chosen optimal cruise altitude: h_c = {h_c} m")
print()
print(f"Lift coefficient : C_L_c = {C_L_c[i_c]:.3f} at h_c")
print(f"Drag coefficient : C_D_c = {C_D_c[i_c]:.3f} at h_c")
print(f"Thrust required for cruise T_c = {T_c[i_c]:.2f} N at h_c")
print(f"Power required for cruise P_c = {P_c[i_c]/1000:.2f} kW or {W_to_hp(P_c[i_c]):.2f} hp at h_c")
print(f"Power to shaft required for cruise P_c_shaft = {P_c_shaft[i_c]/1000:.2f} kW or {W_to_hp(P_c_shaft[i_c]):.2f} hp at h_c")

plt.show()


