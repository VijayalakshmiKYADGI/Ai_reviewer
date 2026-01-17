def process_users():  # Missing docstring (C0116)
    users = []  
    for user in users_list:  # Undefined variable (E0602)
        user_name=user.name.lower()  # Invalid name (C0103)
        if len(user_name)>5:import os  # Import in function (C0415)
        users.append(user_name)
    return users  # Too many return statements (R0911)

def messy_function(x,y): # Missing whitespace (C0326)
    z=x+y
    print(z) # Missing parenthesis in print (E0001 - but this is python 3 compatible if simple)
    return z

class bad_class: # Invalid class name (C0103)
    def __init__(self):
        self.x = 1
