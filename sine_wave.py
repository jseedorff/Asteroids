import numpy as np
import matplotlib.pyplot as plt

# Create 500 evenly spaced x-values between 0 and 4*pi (two full wave cycles)
x = np.linspace(0, 4 * np.pi, 500)

# Calculate the sine of each x-value to get the corresponding y-values
y = np.sin(x)

# Set up the plot with the x and y data
plt.plot(x, y)

# Add labels and a title so the graph is easy to read
plt.title("Sine Wave")
plt.xlabel("x")
plt.ylabel("sin(x)")

# Add a light grid to make the wave easier to follow
plt.grid(True)

# Display the plot in a pop-up window
plt.show()
