import math

# Read the input
names_input = input("Enter student names ")
grade_input = input("Enter student grades ")

grade_list = grade_input.split(",")
grade_list = [float(n) for n in grade_list]

name_list = names_input.split(",")

combined_list = []
for n in range(len(name_list)):
    combined_name_and_grade = [name_list[n], grade_list[n]]
    combined_list.append(combined_name_and_grade)

max_score = 0
max_score_index = 0
min_score = math.inf
min_score_index = 0
for n in range(len(combined_list)):
    if (combined_list[n][1] > max_score):
        max_score = combined_list[n][1]
        max_score_index = n
    if (combined_list[n][1] < min_score):
        min_score = combined_list[n][1]
        min_score_index = n

avgScore = sum(grade_list)/len(grade_list)

def score_to_grade(grade):
    if (grade >= 90.0):
        return "A"
    elif (grade >= 80.0):
        return "B"
    elif (grade >= 70.0):
        return "C"
    elif (grade >= 60.0):
        return "D"
    else:
        return "F"

print("Maximum score is " + str(combined_list[max_score_index][1]) + " (" + score_to_grade(combined_list[max_score_index][1]) + ") scored by " + (combined_list[max_score_index][0]))
print("Minimum score is " + str(combined_list[min_score_index][1]) + " (" + score_to_grade(combined_list[min_score_index][1]) + ") scored by " + (combined_list[min_score_index][0]))
print("Average score is " + str(avgScore))