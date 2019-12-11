
import math
import subprocess
import time
from copy import deepcopy

import matplotlib.pyplot as plt
import numpy as np
import scipy.linalg


# Initial guess
input_vec = [3, 0, 0, 1e-3]

# Resistance in Ohms
R = 30

# Capacitance in Farads
C = 2e-6

# Inductance in Henrys
L = 20e-3

# Initial current
I_0 = 0

# Frequency of the AC source in Hertz
f = 909

# AC peak
Vin_AC_peak = 9*math.sqrt(2)

# DC component
Vin_DC = 0

sin_multiplier = f*2*math.pi

# Combo of AC and DC power source
def get_Vin(t):
    return Vin_AC_peak*math.sin(sin_multiplier*t) + Vin_DC


# Starting time, and size of time steps
t = 1e-5
delta_t = 1e-5

old_v2 = 0
old_v3 = 0

# Holds results for plotting
results = [[],[],[]]

# Create the Jacobian for this input vector
g_ind = L*delta_t/2
g_cap = C/delta_t
jac = np.array([[1/R, -1/R, 0, -1],
                [-1/R, g_ind + 1/R, -g_ind, 0],
                [0, -g_ind, g_ind + g_cap, 0],
                [1, 0, 0, 0]])

start = time.time()
while True:

    # Load the variables from the input vector
    v1 = input_vec[0]
    v2 = input_vec[1]
    v3 = input_vec[2]
    iv = input_vec[3]

    # Calculate the values in result vector
    result_vector = [0, 0, 0, 0]

    result_vector[0] = -((v1-v2)/R - iv) # Current at 1
    result_vector[1] = -(I_0 + L*delta_t/2*(old_v2+v2-v3-old_v3) - (v1-v2)/R) # Current at 2
    result_vector[2] = -(C*(v3-old_v3)/delta_t - I_0 - L*delta_t/2*(old_v2+v2-v3-old_v3)) # Current at 3
    result_vector[3] = -(v1-get_Vin(t)) # Voltage at 1
    
    '''
    # Calculate the new (better) input vector by doing new x = old x - J(x)^(-1)*F(x), where J(x)^(-1) is the inverse Jacobian of x, and F(x) is the result vector given by x
    inv_jac = lapack_inverse(jac)
    res = np.dot(inv_jac, np.array(result_vector))
    input_vec -= res
    '''

    delta_in = scipy.linalg.lapack.dgesv(jac, result_vector)[2]
    input_vec += delta_in

    # If the better guess is indistinguishable from the prior guess, we probably have the right value...
    if (abs(delta_in) < 1e-5).all():
        # Updates the variables like time and the "old" voltages
        t += delta_t
        old_v2 = v2
        old_v3 = v3
        I_0 = I_0 + delta_t/2*(old_v2+v2-v3-old_v3)
        
        results[0].append(t)
        results[1].append(v3)
        results[2].append(iv)

        if t > 60/60:
            print(time.time()-start)
            # Plots nice graph
            fig, ax = plt.subplots(1, 1, figsize=(20, 9))
            ax.scatter(results[0], results[1])
            ax.scatter(results[0], results[2])
            # '''
            plt.show()
            # '''

            '''
            plt.savefig("fig.svg", format='svg', dpi=300)
            subprocess.call(["/usr/bin/open", "fig.svg"])
            '''

            break
