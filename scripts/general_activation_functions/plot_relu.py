# plot inputs and outputs
import matplotlib.pyplot as plt


# rectified linear function
def rectified(x):
    return max(0.0, x)


x = [i for i in range(-10, 11)]
y = [rectified(i) for i in x]
# line plot of raw inputs to rectified outputs
plt.plot(x, y)
plt.savefig("relu.pdf", format="pdf", bbox_inches="tight")
