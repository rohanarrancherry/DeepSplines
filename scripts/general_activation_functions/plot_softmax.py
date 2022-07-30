import numpy as np
import matplotlib.pyplot as plt
from plot_sigmoid import sigmoid

def softmax_cross_entropy(z, y):
    if y == 1:
        return -np.log(z)
    else:
        return -np.log(1 - z)


x = np.arange(-9, 9, 0.1)
a = sigmoid(x)
softmax1 = softmax_cross_entropy(a, 2)
softmax2 = softmax_cross_entropy(a, 1)
figure, axis = plt.subplots(figsize=(7, 7))

plt.plot(a, softmax1, label='i=2')
plt.plot(a, softmax2, label='i=1'   )
plt.xlabel("Cross entropy loss")
plt.ylabel("log loss")
plt.legend(loc="best")
plt.savefig("softmax.pdf", format="pdf", bbox_inches="tight")

