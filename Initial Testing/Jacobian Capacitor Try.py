# https://imgur.com/a/yuzYJ5D

import time
import numpy as np
from copy import deepcopy
import matplotlib.pyplot as plt

# Resistance in ohms of the resistor
r = 1
# Capacitance of the capacitor
C = 1

Vin = 10

b = 0

old_v2 = 0
delta_t = 5e-3
t = 5e-3

# Initial guess for the first step (literally doesn't matter)
input_vec = [10, 5, -2]

results = [[],[]]

s = time.time()
while True:
    # Load the variables from the input vector
    v1 = input_vec[0]
    v2 = input_vec[1]
    iv = input_vec[2]

    # Calculate the values in result vector
    result_vector = [0, 0, 0]

    result_vector[0] = (v1-v2)/r + iv
    result_vector[1] = (v2-v1)/r + C * (v2-old_v2)/delta_t
    result_vector[2] = v1 - Vin

    # Create the Jacobian for this input vector
    jac = np.array([[1/r,-1/r,1],[-1/r,1/r+C/delta_t,0],[1,0,0]])
    inv_jac = np.linalg.inv(jac)

    res = inv_jac @ np.array(result_vector)
    old_input_vec = deepcopy(input_vec)
    input_vec -= res

    if np.allclose(old_input_vec, input_vec, rtol=0, atol=1e-10):
        results[0].append(t)
        results[1].append(v2)

        if t>=1+b:
            b += 1

            Vin = 0 if Vin == 10 else 10

            print(f"t = {t}")
            print(input_vec)
            print(result_vector)
            print(time.time()-s)
            #x = input()
            if t >= 20:
                fig, ax = plt.subplots(1, 1, figsize=(30,10))
                ax.scatter(results[0], results[1])
                
                plt.show()

                peaks = []
                b4 = -1
                up = True
                for i in results[1]:
                    if up:
                        if i > b4:
                            b4 = i
                        else:
                            peaks.append(b4)
                            up = False
                    else:
                        if i > b4:
                            up = True
                
                print(peaks)

                break

        t += delta_t
        old_v2 = v2


    '''
    inv_jac = jac.inv()
    res = jac * sp.Matrix(result_vector)
    input(res)
    input_vec = input_vec - res
    print(input_vec)
    print(result_vector)
    input()
    '''
