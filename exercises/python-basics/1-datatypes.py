"""Datatypes and assignment"""

# This file demonstrates the use of different data types in Python.

# TODO: Write correct value types to variables.

a = "Hello, world!"  # String
b = 5              # Integer
c = 5.0            # Float
d = True           # Boolean

# TODO: Print values.
print(a)
print(b)
print(c)
print (d)

# TODO: Print types of values.
print(type(a))
print(type(b))
print(type(c))
print(type(d))

# ----------------------------------------------

"""Lists and dictionaries"""

# TODO: Make a list of 5 numbers and a string and assign it to a variable.
print("\n")
print("list:")
my_list = [5, 11, 17, 23, "hello"]        # List

# TODO: Print the length of the list.
print(my_list)
print(len(my_list))

#TODO: Print the first and last elements of the list.
print(my_list[0])   #0 is first element
print(my_list[-1])  #-1 is last element
print(my_list[1])   #1 is second element
print(my_list[4])   #4 is fifth element and here also last element


# TODO: Make a dictionary with 3 key-value pairs and assign it to a variable.
my_dict = {"Name": "Alice", "Age": 30, "City": "New York"}        # Dictionary

# TODO: Print keys, values, key-value pairs.
print()
print("dictionary:")
print(my_dict.keys())
print(my_dict.values())
print(my_dict.items())

print(my_dict["Name"])  # Accessing value by key
print(my_dict["Age"])   
print (my_dict["City"])





