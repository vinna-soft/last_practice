import re
from datetime import datetime

# --- mobile validation ---
def is_valid_mobile(mobile):
    return re.match(r"^[9876]\d{9}$", mobile)

#----name validation----
def is_valid_name(name):
    if len(name) < 3:
        return False
    if not name.isalpha():
        return False
    return True

#---email validation----
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)

# --- password validation ---
def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Za-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

#----date validation------
def is_valid_date(date):
    if date == "":
        return False
    today = datetime.today().date()
    booking_date = datetime.strptime(date, "%Y-%m-%d").date()

    if booking_date < today:
        return False
    return True

#-------time valildation--------
def is_valid_time(time):
    if time =="":
        return False
    return True 


#---------address validations-------

def is_valid_address(address):
    if address.strip() == "":
        return False
    if len(address) < 5:
        return False
    return True

#----------provider verification validations----------
#============  adhaar validations==============
def is_valid_aadhar(aadhar):
    return re.match(r"^\d{12}$", aadhar)


# -------- PAN validation --------
def is_valid_pan(pan):
    return re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", pan)


# -------- Bank Account validation --------
def is_valid_bank_account(account):
    return re.match(r"^\d{9,18}$", account)


# -------- IFSC validation --------
def is_valid_ifsc(ifsc):
    return re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", ifsc)

