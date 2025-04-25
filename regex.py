'''regex'''
import re

def validate_name(name):
    ''' complitad regex for username min. 3 char and max. 30, special
    characters can be allowed, if all characters are only special 
    characters it should return false'''
    if not name:
        return None
    regex = "^[A-Za-z0-9]{1,30}$"
    return re.fullmatch(regex, name) is not None

def validate_email(email):
    '''regex for email'''
    regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.fullmatch(regex, email) is not None

def validate_password_1(password):
    '''Minimum eight and maximum 10 characters, at least one
    uppercase letter, one lowercase letter, one number and one special character:'''
    regex = r"^.{8,20}$"
    return re.fullmatch(regex, password) is not None
def validate_password_2(password):
    '''Minimum eight and maximum 10 characters, at least one
    uppercase letter, one lowercase letter, one number and one special character:'''
    regex = r"^(?=.*\d).+$"
    return re.fullmatch(regex, password) is not None
def validate_password_3(password):
    '''Minimum eight and maximum 10 characters, at least one
    uppercase letter, one lowercase letter, one number and one special character:'''
    regex = r"^(?=.*[A-Z]).+$"
    return re.fullmatch(regex, password) is not None
def validate_password_4(password):
    '''Minimum eight and maximum 10 characters, at least one
    uppercase letter, one lowercase letter, one number and one special character:'''
    regex = r"^[a-zA-Z0-9]+$"
    return re.fullmatch(regex, password) is not None
def validate_number(number):
    '''must be checked '''
    regex = r"^\+?[0-9]{10,15}$"
    return re.fullmatch(regex, number) is not None
