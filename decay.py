# exponential decay function
# decay.py

import time

def decay(max_kl, max_time, half_life):
    t = int(time.time())
    return max_kl * ((1.0/2) ** ((t - max_time) / half_life))
