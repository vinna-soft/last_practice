from flask import Flask, Blueprint, render_template, request, redirect, session
from config.database import connection
from utils.validations import *

auth = Blueprint("auth", __name__)

@auth.route("/")
def home():
    return redirect("/register")

#---------------customer Register Page------------
@auth.route("/register", methods=["GET", "POST"])
def register():
    name_error = ""
    mobile_error = ""
    password_error = ""
    email_error = ""
    city_error = ""
    address_error = ""
    zone_error = ""
    msg = ""

    name=""
    mobile=""
    email=""
    password=""
    city = ""
    address = ""
    zone_id = ""

    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT zone_id, zone_name FROM zones")
    zones = cursor.fetchall()

    if request.method == "POST":

        name = request.form['name'].strip()
        mobile = request.form['mobile'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        city = request.form['city'].strip()
        address = request.form['address'].strip()
        zone_id = request.form.get('zone_id')           #------can be empty also

        cursor = connection.cursor()

        if name == "":
            name_error = "Name is required"
        elif not is_valid_name(name):
            name_error = "name must contains letters, and, at least 3 charachters"

        if mobile == "":
            mobile_error = "MObile number required"
        elif not is_valid_mobile(mobile):
            mobile_error = "Invalid mobile number (must start with 9,8,7,6 and 10 digits)"

        if email == "":
            email_error = "email is required"
        elif not is_valid_email(email):
            email_error = "Invalid email format"
        if city =="":
            city_error = "City is required"
        
        if zone_id == "":
            zone_id =None

        if address =="":
            address_error = "address is required"

        if password =="":
            password_error = "Password is required"
        elif not is_valid_password(password):
            password_error = "Password must be at least 8 characters,and include a letter,special character and number"

        if name_error =="" and mobile_error == "" and email_error=="" and password_error == "" and city_error=="" and zone_error =="":
            

            # Check if mobile & email already exists
            cursor.execute("SELECT * FROM customers WHERE mobile=%s", (mobile,))
            customer_mobile = cursor.fetchone()

            cursor.execute("SELECT * FROM customers WHERE email=%s", (email,))
            customer_email = cursor.fetchone()

            if customer_mobile:
                mobile_error = "Mobile number already exists"
            elif customer_email:
                email_error = "Email already exists"
            else:
                cursor.execute(
                    "INSERT INTO customers (name, mobile,email, password, city, address, zone_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (name, mobile, email, password, city, address, zone_id)
                )
                connection.commit()

                customer_id = cursor.lastrowid

                receiver_id = None
                receiver_type = None

                # --------------Check Zone Admin----------------
                if zone_id:
                    cursor.execute("""
                       SELECT admin_id FROM admins 
                       WHERE zone_id = %s AND status = 'active'
                    """, (zone_id,))

                    zone_admin = cursor.fetchone()
    
                    if zone_admin:
                        receiver_id = zone_admin[0]
                        receiver_type = "zone_admin"

                # --------------If no zone admin → City Admin------------
                if not receiver_id:
                    cursor.execute("""
                        SELECT admin_id FROM admins 
                        WHERE city = %s AND status = 'active' AND zone_id IS NULL
                    """, (city,))
    
                    city_admin = cursor.fetchone()
    
                    if city_admin:
                        receiver_id = city_admin[0]
                        receiver_type = "city_admin"

                # ----------------If no city admin → Super Admin----------------
                if not receiver_id:
                    cursor.execute("""
                       SELECT super_admin_id FROM super_admins 
                       WHERE status = 'active' LIMIT 1
                    """)
                    super_admin = cursor.fetchone()
                    if super_admin:
                        receiver_id = super_admin[0]
                        receiver_type = "super_admin"

                if zone_id:
                    message = f"New customer registrered :{name} ({city} - Zone{zone_id})"
                else:
                    message = f"New customer registrered :{name} ({city})"
                if receiver_id:
                    cursor.execute("INSERT INTO notifications(receiver_id, sender_id,booking_id, message, type, receiver_type) VALUES (%s, %s, %s, %s, %s, %s)", (receiver_id, customer_id, None, message, "new_customer", receiver_type))
                connection.commit()
                msg = "Registration Successfully"
            
            if msg == "Registration Successfully":
                return redirect("/login")
               
    return render_template(
        "register.html", name=name, name_error=name_error, mobile=mobile, mobile_error=mobile_error,
        email= email, email_error=email_error, password=password, password_error=password_error, zones = zones, 
        city=city, city_error = city_error,address_error=address_error, msg=msg
    )

@auth.route("/provider/register", methods=["GET", "POST"])
def provider_register():
    name_error = ""
    mobile_error = ""
    password_error = ""
    email_error = ""
    address_error = ""
    experience_error = ""
    service_area_error = ""
    inclusions_error = ""
    price_error = ""
    msg = ""

    name=""
    mobile=""
    email=""
    password=""
    address = ""
    experience = ""
    price = ""
    city= ""
    zone_id = ""
    inclusions = ""

    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT service_id, service_name FROM services")
    services = cursor.fetchall()

    cursor.execute("SELECT zone_id, zone_name FROM zones")
    zones = cursor.fetchall()
    cursor.close()


    if request.method == "POST":

        name = request.form['name'].strip()
        mobile = request.form['mobile'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        address = request.form['address'].strip()
        service_id = request.form['service_id'].strip()
        inclusions = request.form['inclusions'].strip()
        experience = request.form['experience'].strip()
        price = request.form['price'].strip()
        city = request.form.get('city', '').strip()
        zone_id = request.form.get('zone_id')   
    

        if name == "":
            name_error = "Name is required"
        elif not is_valid_name(name):
            name_error = "name must contains letters, and, at least 3 charachters"

        if mobile == "":
            mobile_error = "MObile number required"
        elif not is_valid_mobile(mobile):
            mobile_error = "Invalid mobile number (must start with 9,8,7,6 and 10 digits)"

        if email == "":
            email_error = "email is required"
        elif not is_valid_email(email):
            email_error = "Invalid email format"

        if password =="":
            password_error = "Password is required"
        elif not is_valid_password(password):
            password_error = "Password must be at least 8 characters,and include a letter,special character and number"
        
        if not experience:
            experience_error = "Experience required"
        if not city:
            service_area_error = "City required"
        if price == "":
            price_error = "Price is required"

        if zone_id == "":
            zone_id =None

        if inclusions =="":
            inclusions_error = "Work iclusions is required"

        if name_error =="" and mobile_error == "" and email_error=="" and password_error == "" and address_error=="" and experience_error =="" and service_area_error == "" and inclusions_error=="" and price_error=="":
            cursor = connection.cursor()

            # Check if mobile & email already exists
            cursor.execute("SELECT * FROM providers WHERE mobile=%s", (mobile,))
            provider_mobile = cursor.fetchone()

            cursor.execute("SELECT * FROM providers WHERE email=%s", (email,))
            provider_email = cursor.fetchone()

            if provider_mobile:
                mobile_error = "Mobile number already exists"
            elif provider_email:
                email_error = "Email already exists"
            else:
                cursor.execute(
                    "INSERT INTO providers (name, mobile, email, password, address, service_id, inclusions, price, experience, city, zone_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (name, mobile, email, password, address, service_id, inclusions, price, experience, city, zone_id)
                )
                connection.commit()

                provider_id= cursor.lastrowid
                receiver_id = None
                receiver_type = None

                # --------------Check Zone Admin----------------
                if zone_id:
                    cursor.execute("""
                       SELECT admin_id FROM admins 
                       WHERE zone_id = %s AND status = 'active'
                    """, (zone_id,))

                    zone_admin = cursor.fetchone()
    
                    if zone_admin:
                        receiver_id = zone_admin[0]
                        receiver_type = "zone_admin"

                # --------------If no zone admin → City Admin------------
                if not receiver_id:
                    cursor.execute("""
                        SELECT admin_id FROM admins 
                        WHERE city = %s AND status = 'active' AND zone_id IS NULL
                    """, (city,))
    
                    city_admin = cursor.fetchone()
    
                    if city_admin:
                        receiver_id = city_admin[0]
                        receiver_type = "city_admin"

                # ----------------If no city admin → Super Admin----------------
                if not receiver_id:
                    cursor.execute("""
                       SELECT super_admin_id FROM super_admins 
                       WHERE status = 'active' LIMIT 1
                    """)
                    super_admin = cursor.fetchone()
                    if super_admin:
                        receiver_id = super_admin[0]
                        receiver_type = "super_admin"
                if zone_id:
                    message = f"New provider registrered :{name} ({city} - Zone{zone_id})"
                else:
                    message = f"New provider registrered :{name} ({city})"
                
                if receiver_id:
                    cursor.execute("INSERT INTO notifications(receiver_id, sender_id,booking_id, message, type, receiver_type) VALUES (%s, %s, %s, %s, %s, %s)", (receiver_id, provider_id, None, message, "new_provider", receiver_type))
                connection.commit()
                msg = "Registration Successfully"
            if msg == "Registration Successfully":
                return redirect("/login")
        
    return render_template(
        "provider/register.html", name=name, name_error=name_error, mobile=mobile, mobile_error=mobile_error,
        email= email, email_error=email_error,services=services, password=password, password_error=password_error, zones=zones, 
        address=address, address_error = address_error, service_area_error=service_area_error, experience_error=experience_error,
        inclusions=inclusions, inclusions_error=inclusions_error, price=price, price_error=price_error, msg=msg
    )

# Login page
@auth.route("/login", methods=["GET", "POST"])
def login():

    mobile_error = ""
    password_error = ""

    if request.method == "POST":
        mobile = request.form["mobile"]
        password = request.form["password"]

        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM customers WHERE mobile = %s", (mobile, ))
        customer = cursor.fetchone()


        if customer:
            #------check if account is active---
            if customer.get("status") != "active":
                mobile_error = "Your account has been deactivated by admin."
                cursor.close()
                return render_template("login.html", mobile_error=mobile_error, password_error=password_error)
            
             
            if customer["password"] == password:
                session["user_id"] = customer["id"]
                session["role"] = "customer"
                session["city"] = customer["city"]
                session["zone_id"] = customer["zone_id"]
                session["name"] = customer["name"]

                print(session)
                cursor.close()
                return redirect("/home_page")
            else:
                password_error = "Invalid password"
                cursor.close()
                return render_template("login.html",mobile_error=mobile_error, password_error=password_error )
               
            
        cursor.execute(" SELECT * FROM providers WHERE mobile =%s", (mobile,))
        provider = cursor.fetchone()
    
        if provider:
             #------check if account is active---
            if provider.get("status") != "active":
                mobile_error = "Your account has been deactivated by admin."
                cursor.close()
                return render_template("login.html", mobile_error=mobile_error, password_error=password_error)


            if provider["password"] == password:
                session["role"] = "provider"
                session["name"] = provider["name"]
                session["city"] = provider["city"]
                session["zone_id"] = provider["zone_id"]
                session["provider_id"] = provider["provider_id"]

                print(session)
                cursor.close()
                return redirect("/provider/dashboard")
            else:
                password_error = "Invalid password"
                cursor.close()
                return render_template("login.html",mobile_error=mobile_error, password_error=password_error )
        
        cursor.execute("SELECT * FROM admins WHERE mobile = %s AND status = 'active'", (mobile,))
        admin = cursor.fetchone()

        if admin:
            #-----------check city assignment-------
            if not admin.get("city"):
                mobile_error = "Admin city is not assigned.Contact super admin."
                cursor.close()
                return render_template("login.html", mobile_error=mobile_error, password_error=password_error)
            
            
            if admin["password"] == password:
                session["name"] = admin["name"]
                session["city"] = admin["city"]
                session["zone_id"] = admin["zone_id"]
                session["admin_id"] = admin["admin_id"]

                #------------role logic-----
                if admin["zone_id"]:
                    session["role"] = "zone_admin"
                else:
                    session["role"] = "city_admin"

                print(session)
                cursor.close()
                return redirect("/admin/dashboard")
            else:
                password_error = "Invalid password"
                cursor.close()
                return render_template("login.html",mobile_error=mobile_error, password_error=password_error )
            

        cursor.execute("SELECT * FROM super_admins WHERE mobile = %s AND status = 'active'", (mobile,))
        super_admin = cursor.fetchone()

        if super_admin:
            if super_admin["password"] == password:
                session["role"] = "super_admin"
                session["name"] = super_admin["name"]
                session["super_admin_id"] = super_admin["super_admin_id"]

                print(session)
                cursor.close()
                return redirect("/super_admin/dashboard")
            else:
                password_error = "Invalid password"
                cursor.close()
                return render_template("login.html",mobile_error=mobile_error, password_error=password_error )
            

         # if mobile number not found in any table   
        mobile_error = "Mobile number not found"
        cursor.close()
    return render_template("login.html", mobile_error=mobile_error, password_error=password_error)
    

@auth.route("/show_cookie")
def show_cookie():
    return request.cookies

@auth.route("/check_session")
def check_session():
    return str(session)

@auth.route("/logout")
def logout():
    session.clear()
    return redirect ("/login")


