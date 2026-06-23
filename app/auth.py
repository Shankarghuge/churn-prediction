import re

# Authenticate User
def name_valid(name):
    if name.isalpha() and len(name) > 2:
        return True
    else:
        return False

def password_valid(pass1):
    reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
    pat = re.compile(reg)
    mat = re.search(pat, pass1)
    if mat:
        return True
    else:
        return False

def password_check(password1, password2):
    if password1 == password2:
        return True
    else:
        return False

def authentication(first_name, last_name, pass1, pass2):
    if not name_valid(first_name):
        return "Invalid First Name"
    elif not name_valid(last_name):
        return "Invalid Last Name"
    elif not password_valid(pass1):
        return "Password should be in proper format (e.g., Password@1234)"
    elif not password_check(pass1, pass2):
        return "Passwords do not match"
    else:
        return "success"
