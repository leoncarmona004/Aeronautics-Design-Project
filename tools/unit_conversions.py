
# ============================================================
# UNIT CONVERSION FUNCTIONS
# ============================================================

# -------------------------
# MASS
# -------------------------

def lb_to_kg(lb):
    return lb * 0.45359237

def kg_to_lb(kg):
    return kg / 0.45359237

# -------------------------
# DISTANCE
# -------------------------

def ft_to_m(ft):
    return ft * 0.3048

def m_to_ft(m):
    return m / 0.3048

def nmi_to_ft(nmi):
    return nmi * 6076.11549

def ft_to_nmi(ft):
    return ft / 6076.11549

def nmi_to_m(nmi):
    return nmi * 1852

def m_to_nmi(m):
    return m / 1852

# -------------------------
# SPEED
# -------------------------

def kt_to_ms(kt):
    return kt * 0.514444444444

def ms_to_kt(ms):
    return ms / 0.514444444444

def kmh_to_ms(kmh):
    return kmh / 3.6

def ms_to_kmh(ms):
    return ms * 3.6

# -------------------------
# FORCE
# -------------------------

def lbf_to_N(lbf):
    return lbf * 4.44822161526

def N_to_lbf(N):
    return N / 4.44822161526

# -------------------------
# POWER
# -------------------------

def hp_to_W(hp):
    return hp * 745.699871582

def W_to_hp(W):
    return W / 745.699871582
