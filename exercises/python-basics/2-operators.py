"""Arithmetic Operators"""

# Arithmetic operations are performed using the following operators: 
# +, -, *, / (addition, subtraction, multiplication, division), ** (exponent), % (modulus), // (floor division)

a = 10
b = 5.5

# TODO: Write an addition operation using the above variables.
addition = a + b
print(addition)

# TODO: Write a subtraction operation using the above variables.
subtraction = a - b
print(subtraction)

# TODO: Write a multiplication operation using the above variables.
multiplication = a * b
print(multiplication)
print()

#square
d_squared = a ** 2
print(d_squared)

#%
modulus = a % b #Rest nach ganzzaliger Division
print(modulus)
print()


# ----------------------------------------------

"""Comparison operators"""

# Comparison operators are used to compare two values. The result of a comparison is a Boolean value (True or False).

x = 100
y = 100

# TODO: Write an equal to comparison using the above variables.
equal = x == y
print("x is equal to y: ", equal)

# TODO: Write a not equal to comparison using the above variables.
not_equal = x != y
print("x is not equal to y: ", not_equal)


# TODO: Write a greater than comparison using the above variables.
greater_than = x > y
print("x is greater than y: ", greater_than)

# TODO: Write a less than or equal to comparison using the above variables.
less_or_equal = x <= y
print("x is less than or equal to y: ", less_or_equal)

# ----------------------------------------------

"""Logical operators"""

# Logical operators are used to combine conditional statements. The result of a logical operation is a Boolean value (True or False).

# TODO: Write a logical AND operation using True and False.
logical_and = True and False
print("Logical AND: ", logical_and)

# TODO: Write a logical OR operation using True and False.
logical_or = True or False
print("Logical OR: ", logical_or)

# TODO: Write a logical NOT operation using True.
logical_not = not True
print("Logical NOT: ", logical_not)
print()


# ----------------------------------------------

"""Identity operators"""

# Identity operators are used to compare the memory locations of two objects. The result of an identity operation is a Boolean value (True or False).
a = 1
b = 20

# TODO: Write an IS identity comparison using the above variables.
is_same = a is b
print(is_same)

# TODO: Write a IS NOT identity comparison using the above variables.
is_not_same = a is not b
print(is_not_same)

# ----------------------------------------------

"""Membership operators"""

# Membership operators are used to test whether a sequence is presented in an object. The result of a membership operation is a Boolean value (True or False).

my_list = [1, 2, 3, 4, 5, 10]  # List datatype

# TODO: Write an IN membership operation to check if a is in my_list.
is_in_list = a in my_list
print(is_in_list)

# TODO: Write a NOT IN membership operation to check if b is not in my_list.
is_not_in_list = b not in my_list
print(is_not_in_list)
