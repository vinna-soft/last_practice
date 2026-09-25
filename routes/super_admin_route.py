from flask import Flask, Blueprint, render_template, request, redirect, session
from config.database import connection
from utils.validations import *
import requests
from datetime import datetime

super_admin = Blueprint("super_admin", __name__)


@super_admin.route("/super_admin/dashboard")
def admin_dashboard():
    if "super_admin_id" not in session:
        return redirect("/login")
    
    cursor = connection.cursor(dictionary=True)

    # ------total customers-----------
    cursor.execute("SELECT COUNT(*) AS total FROM customers")
    total_customers = cursor.fetchone()["total"]

    #----total providers----
    cursor.execute("""SELECT COUNT(*) AS total
        FROM providers
        WHERE verification_status = 'approved'
    """)
    total_providers = cursor.fetchone()["total"]

    #--------------total admins---------------------
    cursor.execute("SELECT COUNT(*) AS total FROM admins")
    total_admins = cursor.fetchone()["total"]
    

    #-------------total cities----------------
    cursor.execute("SELECT COUNT(*) AS total FROM cities")
    total_cities = cursor.fetchone()["total"]
    cursor.close()

    return render_template("super_admin/dashboard.html", total_customers=total_customers, total_providers=total_providers, total_admins=total_admins, total_cities=total_cities)



# -------add city--------
@super_admin.route("/super_admin/add_city", methods = ["GET", "POST"])
def add_city():
    if "super_admin_id" not in session:
        return redirect("/login")
    
    cursor = connection.cursor(dictionary=True)
    message = ""

    if request.method == "POST":
        city_name = request.form["city_name"]
        state = request.form["state"]

        # check duplicate city
        cursor.execute("SELECT * FROM cities WHERE city_name = %s", (city_name, ))
        existing_city = cursor.fetchone()

        if existing_city:
            message = "City already exists."

        else:
            cursor.execute("INSERT INTO cities (city_name, state) VALUES (%s, %s)", (city_name, state))
            connection.commit()
            message = "City added successfully."
            cursor.close()
    
    return render_template("super_admin/add_city.html", message=message)


@super_admin.route("/super_admin/cities")
def view_cities():
    if "super_admin_id" not in session:
        return redirect("/login")
    
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cities")
    cities = cursor.fetchall()
    cursor.close()
    return render_template("super_admin/view_cities.html", cities=cities)


@super_admin.route("/super_admin/city/activate/<int:city_id>")
def activate_city(city_id):
    if "super_admin_id" not in session:
        return redirect("/login")

    cursor = connection.cursor()
    cursor.execute("UPDATE cities SET status='active' WHERE city_id=%s", (city_id,))
    connection.commit()

    return redirect("/super_admin/cities")


@super_admin.route("/super_admin/city/deactivate/<int:city_id>")
def deactivate_city(city_id):
    if "super_admin_id" not in session:
        return redirect("/login")

    cursor = connection.cursor()
    cursor.execute("UPDATE cities SET status='inactive' WHERE city_id=%s", (city_id,))
    connection.commit()

    return redirect("/super_admin/cities")

@super_admin.route("/super_admin/add_zone", methods = ["GET", "POST"])
def add_zone():
    if "super_admin_id" not in session:
        return redirect("/login")

    cursor = connection.cursor(dictionary=True)
    message = ""

    if request.method == "POST":
        zone_name = request.form["zone_name"]
        city_id = request.form["city_id"]

        # --------check duplicate zone-------
        cursor.execute("SELECT * FROM zones WHERE zone_name = %s AND city_id = %s", (zone_name, city_id))
        existing_zone = cursor.fetchone()

        if existing_zone:
            message = "Zone already exists in this city."

        else:
            cursor.execute("INSERT INTO zones (city_id, zone_name) VALUES (%s, %s)", (city_id, zone_name))
            connection.commit()
            message = "Zone added successfully."
            cursor.close()

    # --------Fetch all cities for the dropdown---------
    cursor.execute("SELECT * FROM cities WHERE status = 'active'")
    cities = cursor.fetchall()
    cursor.close()

    return render_template("super_admin/add_zone.html", message=message, cities=cities)

@super_admin.route("/super_admin/zones")
def view_zones():
    if "super_admin_id" not in session:
        return redirect("/login")
    
    cursor= connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT zones.zone_id, zones.zone_name, cities.city_name, cities.state, zones.status
        FROM zones
        JOIN cities ON zones.city_id = cities.city_id
    """)
    zones = cursor.fetchall()
    cursor.close()
    return render_template("super_admin/view_zones.html", zones=zones)


@super_admin.route("/super_admin/zone/activate/<int:zone_id>")
def activate_zone(zone_id):
    if "super_admin_id" not in session:
        return redirect("/login")

    cursor = connection.cursor()
    cursor.execute("UPDATE zones SET status='active' WHERE zone_id=%s", (zone_id,))
    connection.commit()

    return redirect("/super_admin/zones")


@super_admin.route("/super_admin/zone/deactivate/<int:zone_id>")
def deactivate_zone(zone_id):
    if "super_admin_id" not in session:
        return redirect("/login")

    cursor = connection.cursor()
    cursor.execute("UPDATE zones SET status='inactive' WHERE zone_id=%s", (zone_id,))
    connection.commit()

    return redirect("/super_admin/zones")

@super_admin.route("/super_admin/add_admin", methods = ["GET", "POST"])
def add_admin():
    if "super_admin_id" not in session:
        return redirect("/login")
    cursor = connection.cursor(dictionary=True)
    message = ""

    #--------fetch active cities--------
    cursor.execute("SELECT * FROM cities WHERE status = 'active'")
    cities = cursor.fetchall()

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        password = request.form["password"]

    #------------check duplicate mobile----------
        cursor.execute("SELECT * FROM admins WHERE mobile = %s", (mobile,))
        mobile_exists = cursor.fetchone()

        if mobile_exists:
            message = "mobile number already exists."
            
        else:
            cursor.execute("INSERT INTO admins (name, email, mobile, password) VALUES (%s, %s, %s, %s)", (name, email, mobile, password))
            connection.commit()
            message = "Admin added successfully."
            cursor.close()
    return render_template("super_admin/add_admin.html", message=message, cities=cities)

#-------view city admins----
@super_admin.route("/super_admin/admins")
def view_admins():
    if "super_admin_id" not in session:
        return redirect ("/login")
    
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM admins")
    admins = cursor.fetchall()
    cursor.close()
    return render_template("super_admin/view_admins.html", admins=admins)



#--------------------view all admins-----------------------
@super_admin.route("/super_admin/admins/view/<int:admin_id>", methods=["GET", "POST"])
def view_admin(admin_id):
    if "super_admin_id" not in session:
        return redirect("/login")
    
    cursor = connection.cursor(dictionary=True)

    # get admin details by admin_id
    cursor.execute("""
        SELECT a.*, z.zone_name
        FROM admins a
        LEFT JOIN zones z ON a.zone_id = z.zone_id
        WHERE a.admin_id = %s
    """, (admin_id,))

    admin = cursor.fetchone()
    cursor.close()

    return render_template("super_admin/admin_details.html", admin=admin)

@super_admin.route("/super_admin/admin/activate/<int:admin_id>")
def activate_admin(admin_id):
    if "super_admin_id" not in session:
        return redirect("/login")

    cursor = connection.cursor()
    cursor.execute("UPDATE admins SET status='active' WHERE admin_id=%s", (admin_id,))
    connection.commit()

    return redirect("/super_admin/admins")


@super_admin.route("/super_admin/admin/deactivate/<int:admin_id>")
def deactivate_admin(admin_id):
    if "super_admin_id" not in session:
        return redirect("/login")

    cursor = connection.cursor()
    cursor.execute("UPDATE admins SET status='inactive' WHERE admin_id=%s", (admin_id,))
    connection.commit()
    return redirect("/super_admin/admins")


@super_admin.route("/super_admin/assign_admin", methods = ["GET", "POST"])
def assign_admin():
    if "super_admin_id" not in session:
        return redirect("/login")

    cursor = connection.cursor(dictionary=True)
    message = ""
    zones = []
    selected_city = request.args.get("city_id")   # GET


    #---------GET : check zone for selected city ------
    if selected_city:
        cursor.execute("SELECT * FROM zones WHERE city_id = %s", (selected_city, ))
        zones = cursor.fetchall()
    
    #-------POST : assign -------------------------
    
    if request.method == "POST":
        city_id = request.form.get("city_id")
        zone_id = request.form.get("zone_id")
        admin_id = request.form.get("admin_id")

        selected_city = city_id  # keep selected

     #----get city name-------------
        cursor.execute("SELECT city_name FROM cities WHERE city_id = %s", (city_id, ))
        city_data = cursor.fetchone()
        city_name = city_data["city_name"]

     #---------check zone for selected city ------
        
        cursor.execute("SELECT * FROM zones WHERE city_id = %s", (city_id, ))
        zones = cursor.fetchall()

        #----------case 1: city has zones- assign zone to admin------
        if zones:
            if not zone_id:
                message = "please select a zone for this city"
            
            else:
                cursor.execute("""
                    SELECT * FROM admins
                    WHERE zone_id = %s
                """, (zone_id, ))
                existing = cursor.fetchone()

                if existing:
                    message = "This zone already has an admin assigned"
                else:
                    cursor.execute("""
                        UPDATE admins
                        SET city = %s, zone_id = %s
                        WHERE admin_id = %s
                    """,(city_name, zone_id, admin_id))
                    connection.commit()
                    message = "Admin assigned to zone successfully"

    #-----case-2:city has no zones - assign ciyt only------
        else:
        #----------check if city already has admin-------
            cursor.execute("""
                SELECT * FROM admins
                WHERE city = %s AND zone_id IS NULL
            """, (city_name, ))
            existing = cursor.fetchone()

            if existing:
                    message = "This city already has an admin assigned"
            
            else:
                cursor.execute("""
                    UPDATE admins
                    SET city = %s, zone_id = NULL
                    WHERE admin_id = %s
                """, (city_name, admin_id))
                connection.commit()
                message = "Admin assigned to city successfully"

    #-----get admins not assigned----------
    cursor.execute("SELECT * FROM admins WHERE city IS NULL OR city = ''")
    admins = cursor.fetchall()

    #---------get cities----------
    cursor.execute("SELECT * FROM cities WHERE status = 'active'")
    cities = cursor.fetchall()

    cursor.close()

    return render_template("super_admin/assign_admin.html", message=message, admins=admins, cities=cities, zones = zones,selected_city=selected_city )




#-------------------Reports------------------------------------------------------

@super_admin.route("/super_admin/reports")
def reports():
    if "super_admin_id" not in session:
        return redirect("/login")
    cursor = connection.cursor(dictionary=True)

    # ----total revenue generated------
    cursor.execute("SELECT SUM(total_amount) AS total_revenue FROM bookings WHERE status = 'completed'")
    total_revenue = cursor.fetchone()['total_revenue'] or 0

    #-----top service------
    cursor.execute("""
        SELECT s.service_name, SUM(b.total_amount) AS revenue
        FROM bookings b
        JOIN services s ON b.service_id = s.service_id
        GROUP BY b.service_id
        ORDER BY revenue DESC
        LIMIT 1
    """)
    top_service = cursor.fetchone()

    #-----total bookings-----
    cursor.execute("SELECT COUNT(*) AS total_bookings FROM bookings")
    total_bookings = cursor.fetchone()["total_bookings"]

    #----active providers------
    cursor.execute("""
        SELECT COUNT(*) AS active_providers
        FROM providers
        WHERE verification_status = 'approved' AND provider_status = 'available'
    """)
    active_providers = cursor.fetchone()["active_providers"]

    #--------most booking provider------
    cursor.execute("""
        SELECT p.name, COUNT(*) AS total_bookings
        FROM bookings b
        JOIN providers p ON b.provider_id = p.provider_id
        GROUP BY b.provider_id
        ORDER BY total_bookings DESC
        LIMIT 1
    """)
    most_booking_provider = cursor.fetchone()
    
    #------city wise reports (Revenue and bookings)------
    cursor.execute("""
        SELECT c.city,COUNT(b.booking_id) AS city_bookings,
        SUM(b.total_amount) AS city_revenue
        FROM bookings b
        JOIN customers c ON b.customer_id = c.id
        WHERE b.status = 'completed'
        GROUP BY c.city
        ORDER BY city_revenue DESC
        
    """)
    city_wise_reports = cursor.fetchall()

  

    #-------monthly revenue -------------
    cursor.execute("""
        SELECT DATE_FORMAT(booking_date, '%Y-%m') AS month, 
        SUM(total_amount) AS revenue
        FROM bookings
        WHERE status = 'completed'
        GROUP BY month
        ORDER BY month
    """)
    monthly_revenue = cursor.fetchall()

    #---------city wise providers list-----
    cursor.execute("""
    SELECT c.city_name, COUNT(p.provider_id) AS providers_count
    FROM cities c
    LEFT JOIN providers p 
        ON LOWER(p.city) = LOWER(c.city_name) 
        AND p.verification_status = 'approved'
    GROUP BY c.city_name
    ORDER BY providers_count DESC
    """)

    provider_reports = cursor.fetchall()

    #----total customers------
    cursor.execute("SELECT COUNT(*) AS total_customers FROM customers")
    total_customers = cursor.fetchone()["total_customers"]

    cursor.close()
    return render_template("super_admin/reports_view.html",
                            total_revenue=total_revenue,
                            top_service=top_service, total_bookings=total_bookings,
                            active_providers=active_providers, total_customers=total_customers, 
                            most_booking_provider=most_booking_provider,provider_reports=provider_reports,
                            city_wise_reports=city_wise_reports, monthly_revenue=monthly_revenue)


#-------------------------------------super admin notifications--------------------------------

@super_admin.route("/super_admin/notifications")
def super_admin_notifications():
    if "super_admin_id" not in session:
        return redirect("/login")
    
    super_admin_id = session["super_admin_id"]
    cursor = connection.cursor(dictionary=True)
    query="""
        SELECT * FROM notifications
        WHERE receiver_id = %s AND receiver_type = 'super_admin'
        ORDER BY created_at DESC
    """
    
    cursor.execute(query, (super_admin_id, ))
    notifications = cursor.fetchall()
    return render_template("super_admin/notification.html", notifications=notifications)

@super_admin.route("/super_admin/add_services", methods=["GET", "POST"])
def add_service():
    if "super_admin_id" not in session:
        return redirect("/login")
    cursor = connection.cursor(dictionary=True)
    message = ""

    if request.method == "POST":
        service_name = request.form["service_name"].strip()

        #---------------check--duplicates-----------
        cursor.execute("""
           SELECT *FROM services
           WHERE LOWER(service_name) = LOWER(%s)
        """, (service_name, ))
        existing = cursor.fetchone()

        if existing:
            message = "Service already exits"
        else:
            cursor.execute("""
              INSERT INTO services(service_name)
              VALUES (%s)
            """, (service_name, ))
            connection.commit()
            message = "Service added successfully"

    #-----fetch all services---------
    cursor.execute("SELECT *FROM services")
    services = cursor.fetchall()
    cursor.close()
    return render_template("super_admin/add_services.html", message=message, services=services)

#----------------view services--------------
@super_admin.route("/super_admin/services")
def view_services():
    if "super_admin_id" not in session:
        return redirect ("/login")
    
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM services")
    services = cursor.fetchall()
    cursor.close()
    return render_template("super_admin/view_services.html", services=services)

@super_admin.route("/super_admin/service/available/<int:service_id>")
def available_service(service_id):
    if "super_admin_id" not in session:
        return redirect("/login")

    cursor = connection.cursor()
    cursor.execute("UPDATE services SET status='available' WHERE service_id=%s", (service_id, ))
    connection.commit()

    return redirect("/super_admin/services")


@super_admin.route("/super_admin/service/unavailable/<int:service_id>")
def unavailable_service(service_id):
    if "super_admin_id" not in session:
        return redirect("/login")

    cursor = connection.cursor()
    cursor.execute("UPDATE services SET status='unavailable' WHERE service_id=%s", (service_id, ))
    connection.commit()
    return redirect("/super_admin/services")


#============admin assign city==================================

@super_admin.route("/super_admin/assign_city_admin", methods = ["GET", "POST"])
def assign_city_admin():
    if "super_admin_id" not in session:
        return redirect("/login")

    cursor = connection.cursor(dictionary=True)
    message = ""

    if request.method == "POST":
        city_name = request.form["city_name"]
        admin_id = request.form["admin_id"]

        # --------check duplicate admin-------
        cursor.execute("SELECT * FROM admins WHERE admin_id = %s AND TRIM(LOWER(city)) = TRIM(LOWER(%s))", (admin_id, city_name))
        admin_existing=cursor.fetchone()

        if admin_existing:
            message = "city already assigned to the admin."

        else:
            cursor.execute("""
               UPDATE admins
               SET city = %s
               WHERE admin_id = %s
            """, (city_name, admin_id))

            connection.commit()
            message = 'City admin assigned successfully.'
    
    #-------------get admins without city------------
    cursor.execute("SELECT * FROM admins WHERE city IS NULL OR city = '' ")
    admins = cursor.fetchall()

    #---------get active cities----------
    cursor.execute("SELECT * FROM cities WHERE status = 'active'")
    cities = cursor.fetchall()

    cursor.close()

    return render_template("super_admin/assign_city_admin.html", message=message, admins=admins, cities=cities)
