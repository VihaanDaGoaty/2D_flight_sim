# Read the input
user_input = input("Enter a list of prices, separated by comma's please  ")

# Process the input
list = user_input.split(",")
try:
    list = [float(n) for n in list]
except:
    print("Enter a list of numbers separated by comma's PLEASE")

# Analyse the input
try:
    avg_value = sum(list)/len(list)
    max_value = max(list)
    min_value = min(list)
except:
    print("THESE ARE NOT NUMEBRS!")

# Return our answer
print("The average is = " + str(avg_value))
print("The max is = " + str(+max_value))
print("The min is = " + str(min_value))