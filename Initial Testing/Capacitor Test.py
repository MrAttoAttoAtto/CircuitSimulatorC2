from scipy import signal
import matplotlib.pyplot as plt
import time
import math

s = time.time()
system = signal.TransferFunction([1], [1, 1])
times, sr = signal.step(system, N=100000)
print(time.time()-s)

fig, ax = plt.subplots(1, 2, figsize=(14, 7))

ax[0].scatter(times, sr, c="red")

eee = [1-math.e**(-t) for t in times]

ax[1].scatter(times, eee, c="green")
plt.show()

print(eee-sr)
