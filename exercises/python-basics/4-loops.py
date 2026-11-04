"""Loops"""

"""While loop"""

# A while-loop is a control flow statement for specifying iteration, which allows code to be executed repeatedly.

# TODO: Write a while loop that prints break_condition and increments it, until it reaches 5

break_condition = 0

while break_condition < 10:
    print(break_condition)
    break_condition += 1
else:
    print("out of while loop")
print()

# ----------------------------------------------

"""For loop"""

# For-loop is a control flow statement for specifying iteration, which allows code to be executed repeatedly.

# TODO: Iterate over pets, printing each one

pets = ["dog", "cat", "horse", "rabbit", "snake"]
print(pets)

for i in pets:
    print(i)


my_list = [34, 71, 81]
for i in my_list:
    print(i-23)

print()


new_list = range(3)
print(range(3))
for i in new_list:
    print(i)
print()

for i in range(3, 10):
    print(i)


point = []
for i in range(3):
    point.append(i)
print(point)