name = input("What's your name? ")
age = int(input("How old are you? "))

next_year_age = age + 1

RED = "\033[31m"
RESET = "\033[0m"

print(RED + "Hello, " + name + "! Welcome to Python :)" + RESET)
print(RED + "Next year, you'll be " + str(next_year_age) + " years old." + RESET)
