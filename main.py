# # first python program
# name = "Velraaj A S"
# age = 23
# city = "Madurai"
# profession = "Junior .NET developer"
# learning_python = True

# print(f"My name is {name}")
# print(f"I am {age} years old")
# print(f"I am living in {city}")
# print(f"I am currently working as a {profession}")
# print(f"Learning Python? {learning_python}")


#Lesson 2: Input, Type Conversion & Operators
# name = str(input("Enter your full name: "))
# age = int(input("Enter your age: "))
# height = float(input("Enter your height (in cms): "))

# print(f"Hello {name}.")
# print(f"You are {age} years old.")
# print(f"Your height is {height:.0f} cms.")


#Lesson 3: Strings & Lists
# skills = ["C#", "SQL", "React"] #List
# print("My Current Skills: ")
# for skill in skills:
#     print(skill)

# skills.append("Python")
# skills.remove("SQL")
# skills.sort()

# print("Final Skills: ")
# for skill in skills:
#     print(skill.upper())

# sentence = "  Python, C#, SQL, React, AI  "
# sentence_list = sentence.split(",")
# for x in sentence_list:
#     print(x.strip().lower()) # this is called method chaining

# if "python" in sentence_list:
#     print(True)


#Lesson 4: Dictionaries, Tuples & Sets
#Methods that modify the object usually return None
#Functions that create a new object usually return it
# employee = {
#     "id": 101,
#     "name": "Velraaj",
#     "department": "AI",
#     "salary": 35000
# }

# employee["salary"] = 40000
# employee["experience"] = 2

# for key, value in employee.items():
#     print(f"{key} : {value}")

# print(employee.get("manager", "Not Assigned"))

# skills = [
#     "Python",
#     "C#",
#     "SQL",
#     "Python",
#     "React",
#     "SQL",
#     "AI"
# ]

# skills = set(skills)
# print(skills)

# final_skill_list = list(skills)
# final_skill_list.sort() # This is will modify the existing list
# sorted(final_skill_list) # This will return a new sorted list
# print(final_skill_list)

#Lesson 5: Control Flow
marks = [78, 45, 92, 67, 88, 34, 99]

for mark in marks:
    print(mark)

for mark in marks:
    if(mark >= 50):
        print(mark)

#Print the index and mark. we use enumerate for this
for index, mark in enumerate(marks, 1):
    print(f"Student {index} -> {mark}")

for mark in marks:
    if(mark >= 90):
        print(f"Topper found: {mark}")
        break

for i in range(1,21):
    if(i%3 == 0):
        continue
    else:
        print(i)

correct_username = "admin"
correct_password = "python123"
login_success = False

for i in range(3):
    username = input("Enter the username: ")
    password = input("Enter your password: ")
    if(username == correct_username and password == correct_password):
        login_success = True
        print("Login Successful")
        break

if(not login_success):
    print("Account Locked")




