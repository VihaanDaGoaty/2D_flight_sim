list = []
sum = 0

for i in range(5):
    user_number_input = int(input("Enter a number"))
    list.append(user_number_input)
    sum = sum + user_number_input

average = sum/len(list)
print(average)