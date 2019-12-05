
import math
import subprocess
import time
from copy import deepcopy

import matplotlib.pyplot as plt
import numpy as np
import scipy.linalg

# The identity matrix
iden = np.eye(3)
# Optimises some of the matrix inversing by only doing some things once and by bypassing sanity checks
def lapack_inverse(A):
    results = scipy.linalg.lapack.dgesv(A, iden)
    if results[3] > 0:
        raise np.linalg.LinAlgError('Singular matrix')
    return results[2]

# Initial guess
input_vec = [4, 2, 3]

# Resistance in Ohms
r = 1e5

# Capacitance of the capacitor in Farads
C = 2.2e-4

# Frequency of the AC source in Hertz
f = 60

# AC peak
Vin_AC_peak = 10

# DC component
Vin_DC = 3

sin_multiplier = f*2*math.pi

# Combo of AC and DC power source
def get_Vin(t):
    return Vin_AC_peak*math.sin(sin_multiplier*t) + Vin_DC

# Set to the starting values of v1 and v2, but will eventually be updated by the new variables
old_v1 = get_Vin(0)
old_v2 = 0

# Starting time, and size of time steps
t = 5e-5
delta_t = 5e-5

# Holds results for plotting
results = [[],[]]

# Create the Jacobian for this input vector (never changes in this circuit because all components are linear)
jac = np.array([[C/delta_t,-C/delta_t,-1],[-C/delta_t,C/delta_t+1/r,0],[1,0,0]])


start = time.time()
while True:

    # Load the variables from the input vector
    v1 = input_vec[0]
    v2 = input_vec[1]
    iv = input_vec[2]

    # Calculate the values in result vector
    result_vector = [0, 0, 0]

    result_vector[0] = C*(v1-old_v1-v2+old_v2)/delta_t-iv
    result_vector[1] = C*(v2-old_v2-v1+old_v1)/delta_t+v2/r
    result_vector[2] = v1-get_Vin(t)

    
    # Calculate the new (better) input vector by doing new x = old x - J(x)^(-1)*F(x), where J(x)^(-1) is the inverse Jacobian of x, and F(x) is the result vector given by x
    inv_jac = lapack_inverse(jac) #np.linalg.inv(jac)
    res = np.dot(inv_jac, result_vector)
    input_vec -= res

    # If the better guess is indistinguishable from the prior guess, we probably have the right value...
    #if np.allclose(old_input_vector, input_vec, rtol=0, atol=1e-10):
    #if d == 2:
    if (res < 1e-5).all():
        results[0].append(t)
        results[1].append(v2)

        # Updates the variables like time and the "old" voltages
        t += delta_t
        old_v1 = v1
        old_v2 = v2
    	
        if t > 60/60:
            print(time.time()-start)
            # Plots nice graph
            fig, ax = plt.subplots(1, 1, figsize=(450, 9))
            ax.scatter(results[0], results[1])
            ax.scatter(results[0], [10*math.sin(60*2*math.pi*(r)) for r in results[0]])

            #'''
            plt.show()
            #'''

            '''
            plt.savefig("fig.svg", format='svg', dpi=300)
            subprocess.call(["/usr/bin/open", "fig.svg"])
            '''

            break
