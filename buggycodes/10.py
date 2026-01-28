def check_password(pwd):
    if len(pwd) < 8:
        return False
    if "password" in pwd:
        return False
    return True
