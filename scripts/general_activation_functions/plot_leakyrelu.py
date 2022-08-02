import matplotlib.pyplot as plt


def leakyrelu(z, alpha):
	return max(alpha * z, z)


x = [i for i in range(-100, 110)]
y = [leakyrelu(i, alpha=0.1) for i in x]
# line plot of raw inputs to rectified outputs
plt.plot(x, y)
plt.grid()
plt.savefig("leakyrelu.pdf", format="pdf", bbox_inches="tight")