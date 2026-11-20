import math
from unit_conversions import *

mass = lb_to_kg(100) 
print(mass)

# Design inputs
W_landing_lb = 10130.0       # [lb] - Project Table 13 (post-takeoff landing assumption = W_to)
g_ft_s2 = 32.174             # [ft/s^2] - Standard gravitational acceleration
V_vert_ft_s = 15.0           # [ft/s] - Raymer Sec. 11.4.2 (p. 369, STOL vertical sink speed)
N_gear = 3.0                 # [-] - Raymer Table 11.5 (General aviation gear load factor)
eta_oleo = 0.75              # [-] - Raymer Table 11.4 (selected mid-range oleo efficiency)
eta_tire = 0.47              # [-] - Raymer Table 11.4 (tire energy absorption efficiency)
P_oleo_psi = 1800.0          # [psi] - Raymer Sec. 11.4.3 (oleo operating pressure)

# Main tire (9.50-16) and static load per main wheel
D_tire_in = 33.35            # [in] - Raymer Table 11.2 (p. 360) and Project Table 17
R_rolling_in = 13.9          # [in] - Raymer Table 11.2 (p. 360)
L_main_static_lb = 4558.6    # [lb] - Project Table 17 (90% total weight split across two main wheels)

IN_TO_CM = 2.54              # [cm/in] - Exact unit conversion factor (1 in = 2.54 cm)
FT_LB_TO_J = 1.355818        # [J/(ft*lb)] - Unit conversion factor from ft*lb to Joules

# 1. Main tire stroke (S_T) and vertical kinetic energy (Raymer Eq. 11.8)
S_tire_in = (D_tire_in / 2.0) - R_rolling_in
KE_vert_ft_lb = 0.5 * (W_landing_lb / g_ft_s2) * (V_vert_ft_s ** 2)

# 2. Total required stroke (Raymer Eq. 11.12 + 1.0 in. margin)
S_gross_in = ((V_vert_ft_s ** 2) / (2.0 * g_ft_s2 * eta_oleo * N_gear)) * 12.0  # 12.0 [in/ft] - ft to in conversion
S_tire_contrib_in = (eta_tire / eta_oleo) * S_tire_in
S_net_in = S_gross_in - S_tire_contrib_in
S_total_in = S_net_in + 1.0  # 1.0 [in] - Raymer Sec. 11.4.2 (standard stroke safety margin)

print(f"S_tire       = {S_tire_in:.3f} in ({S_tire_in * IN_TO_CM:.2f} cm)")
print(f"KE_vertical  = {KE_vert_ft_lb:,.1f} ft*lb ({KE_vert_ft_lb * FT_LB_TO_J:,.1f} J)")
print(f"S_net        = {S_net_in:.3f} in ({S_net_in * IN_TO_CM:.2f} cm)")
print(f"S_total      = {S_total_in:.3f} in ({S_total_in * IN_TO_CM:.2f} cm)\n")

# 3. Direct Oleo (MA=1.0), Trailing-Link (MA=1.5), and Triangulated (MA=1.25)
configurations = {
    "Direct Oleo": 1.0,       # [-] - Unlevered direct oleo baseline (MA = 1.0)
    "Trailing-Link": 1.5,    # [-] - Initial selection per Raymer Sec. 11.4.3 lever/linkage work conservation
    "Triangulated": 1.25,    # [-] - Initial selection per Raymer Sec. 11.4.3 lever/linkage work conservation
}

for name, ma in configurations.items():
    s_oleo_in = S_total_in / ma
    l_oleo_lb = L_main_static_lb * ma
    d_oleo_in = 1.3 * math.sqrt((4.0 * l_oleo_lb) / (P_oleo_psi * math.pi))  # 1.3 [-] - Raymer Eq. (11.13) empirical factor
    l_strut_in = 2.5 * s_oleo_in  # 2.5 [-] - Raymer Sec. 11.4.3 approximate overall strut length factor
    print(f"=== {name} (MA = {ma}) ===")
    print(f"  S_oleo  = {s_oleo_in:.2f} in ({s_oleo_in * IN_TO_CM:.2f} cm)")
    print(f"  L_oleo  = {l_oleo_lb:,.2f} lb")
    print(f"  D_oleo  = {d_oleo_in:.3f} in ({d_oleo_in * IN_TO_CM:.2f} cm)")
    print(f"  L_strut = {l_strut_in:.2f} in ({l_strut_in * IN_TO_CM:.2f} cm)")