import numpy as np
import matplotlib.pyplot as plt


# Hyperbolic Tangent (htan) Activation Function
def tanh(x):
    return (np.exp(x) - np.exp(-x)) / (np.exp(x) + np.exp(-x))


# Generating data for Graph
x_data = np.linspace(-6, 6, 100)
y_data = tanh(x_data)

# Graph
plt.plot(x_data, y_data)
plt.title('Tanh Activation Function')
plt.savefig("tanh.pdf", format="pdf", bbox_inches="tight")
