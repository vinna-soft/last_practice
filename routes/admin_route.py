from flask import Flask, Blueprint, render_template, request, redirect, session
from config.database import connection
from utils.validations import *

admin = Blueprint("admin", __name__)



@admin.route("/admin/dashboard")
def admin_dashboard():
    if "admin_id" not in session:
        return redirect("/login")

    admin_id = session["admin_id"]
    user_name = session.get("admin_name")
    cursor = connection.cursor(dictionary=True)
#-----------------------------------------
    zone_name = None
    if session.get("zone_id"):
        cursor.execute("SELECT zone_name FROM zones WHERE zone_id = %s", (session["zone_id"], ))
        zone = cursor.fetchone()
        if zone:
            zone_name = zone["zone_name"]

    role = session["role"]
    city = session["city"]
    zone_id = session.get("zone_id")
#-----------------------------------

    if role == "city_admin":
        cursor.execute("SELECT COUNT(*) AS total FROM customers WHERE city = %s",(city, ))
        total_customers = cursor.fetchone()["total"]

        #----total providers----
        cursor.execute("SELECT COUNT(*) AS total FROM providers WHERE city = %s", (city, ))
        total_providers = cursor.fetchone()["total"]
        cursor.close()

        #------------------zone admin----------
    elif role == "zone_admin":
        cursor.execute("SELECT COUNT(*) AS total FROM customers WHERE zone_id = %s",(zone_id, ))
        total_customers = cursor.fetchone()["total"]

        #----total providers----
        cursor.execute("SELECT COUNT(*) AS total FROM providers WHERE zone_id = %s", (zone_id, ))
        total_providers = cursor.fetchone()["total"]
        cursor.close()

    return render_template("admin/dashboard.html", user_name=user_name, total_customers=total_customers, total_providers=total_providers, role=role, zone_name=zone_name)

@admin.route("/admin/customers")
def customers():
    if "admin_id" not in session:
        return redirect("/login")
    
    role = session["role"]
    city = session["city"]
    zone_id = session.get("zone_id")

    #---------------------GET sedarch inputs----------
    customer_name = request.args.get("customer_name")
    customer_id = request.args.get("customer_id")

    cursor = connection.cursor(dictionary=True)
    #-----------------------------------------
    zone_name = None
    if session.get("zone_id"):
        cursor.execute("SELECT zone_name FROM zones WHERE zone_id = %s", (session["zone_id"], ))
        zone = cursor.fetchone()
        if zone:
            zone_name = zone["zone_name"]

    role = session["role"]
    city = session["city"]
    zone_id = session.get("zone_id")
#-----------------------------------

    query="""
        select * from customers where """
    params = []
    if role == "city_admin":
        query += "city = %s"
        params.append(city)
    elif role == "zone_admin":
        query += "zone_id = %s"
        params.append(zone_id)
    

    #--------------FILTER BY CUSTOMER NAME-------------
    if customer_name:
        query += " AND customer.name LIKE %s"
        params.append(f"%{customer_name}%")

    #----------------FILTER BY CUSTOMER ID--------------
    if customer_id:
        query += " AND customers.id LIKE %s"
        params.append(customer_id)

    query += " ORDER BY customers.created_at DESC"
    cursor.execute(query, params)
        
    customers = cursor.fetchall()
    return render_template("admin/customers.html", customers=customers, zone_name=zone_name)



@admin.route("/admin/providers")
def providers():
    if "admin_id" not in session:
        return redirect("/login")
    
    role = session["role"]
    city = session["city"]
    zone_id = session.get("zone_id")

    #---------------------GET sedarch inputs----------
    provider_name = request.args.get("provider_name")
    provider_id = request.args.get("provider_id")


    cursor = connection.cursor(dictionary=True)
     #-----------------------------------------
    zone_name = None
    if session.get("zone_id"):
        cursor.execute("SELECT zone_name FROM zones WHERE zone_id = %s", (session["zone_id"], ))
        zone = cursor.fetchone()
        if zone:
            zone_name = zone["zone_name"]

    role = session["role"]
    city = session["city"]
    zone_id = session.get("zone_id")
#-----------------------------------

    query ="""
        SELECT providers.*, services.service_name FROM providers
        JOIN services ON providers.service_id = services.service_id
        where """
    params = []
    if role == "city_admin":
        query += "city = %s"
        params.append(city)
    elif role == "zone_admin":
        query += "zone_id = %s"
        params.append(zone_id)

    #--------------FILTER BY PROVIDERS NAME-------------
    if provider_name:
        query += " AND providers.name LIKE %s"
        params.append(f"%{provider_name}")

    #----------------FILTER BY PROVIDER ID--------------
    if provider_id:
        query += " AND providers.provider_id LIKE %s"
        params.append(provider_id)

    query += " ORDER BY providers.created_at DESC"

    cursor.execute(query, params)
    providers = cursor.fetchall()

    return render_template("admin/service_providers.html", providers=providers, zone_name=zone_name)


@admin.route("/admin/bookings")
def Bookings():
    if "admin_id" not in session:
        return redirect("/login")
    role = session["role"]
    city = session["city"]
    zone_id = session.get("zone_id")


    #---------------------GET sedarch inputs----------
    provider_name = request.args.get("provider_name")
    provider_id = request.args.get("provider_id")


    cursor = connection.cursor(dictionary=True)

     #-----------------------------------------
    zone_name = None
    if session.get("zone_id"):
        cursor.execute("SELECT zone_name FROM zones WHERE zone_id = %s", (session["zone_id"], ))
        zone = cursor.fetchone()
        if zone:
            zone_name = zone["zone_name"]

    role = session["role"]
    city = session["city"]
    zone_id = session.get("zone_id")
#-----------------------------------

    query ="""
        SELECT
            bookings.booking_id,
            customers.name AS customer_name,
            providers.name AS provider_name,
            services.service_name,
            bookings.booking_date,
            bookings.status

        FROM bookings
        JOIN customers ON bookings.customer_id = customers.id
        JOIN providers ON bookings.provider_id = providers.provider_id
        JOIN services ON bookings.service_id = services.service_id
        WHERE """
    
    params = []
    if role == "city_admin":
        query += "providers.city = %s"
        params.append(city)
    elif role == "zone_admin":
        query += "providers.zone_id = %s"
        params.append(zone_id)


    #--------------FILTER BY PROVIDERS NAME-------------
    if provider_name:
        query += " AND providers.name LIKE %s"
        params.append(f"%{provider_name}")

    #----------------FILTER BY PROVIDER ID--------------
    if provider_id:
        query += " AND providers.provider_id LIKE %s"
        params.append(provider_id)

    query += " ORDER BY bookings.created_at DESC"

    cursor.execute(query, params)    
    bookings = cursor.fetchall()
    return render_template("admin/bookings.html", bookings=bookings, zone_name=zone_name)
    


@admin.route("/admin/bookings/view/<int:booking_id>")
def view_booking(booking_id):
    if "admin_id" not in session:
        return redirect("/login")
    role = session["role"]
    city = session["city"]
    zone_id = session.get("zone_id")
    
    cursor = connection.cursor(dictionary=True)
    #-----------------------------------------
    zone_name = None
    if session.get("zone_id"):
        cursor.execute("SELECT zone_name FROM zones WHERE zone_id = %s", (session["zone_id"], ))
        zone = cursor.fetchone()
        if zone:
            zone_name = zone["zone_name"]

    role = session["role"]
    city = session["city"]
    zone_id = session.get("zone_id")
#-----------------------------------

    query = """
        SELECT
            bookings.*,
            customers.name AS customer_name,
            providers.name AS provider_name,
            services.service_name,
            reviews.rating,
            reviews.review
        FROM bookings
        JOIN customers ON bookings.customer_id = customers.id
        JOIN providers ON bookings.provider_id = providers.provider_id
        JOIN services ON bookings.service_id = services.service_id
        LEFT JOIN reviews ON bookings.booking_id = reviews.booking_id
        WHERE bookings.booking_id = %s"""
    params = [booking_id]
    #--------role based serurity filter---------
    if role == "city_admin":
        query += " AND providers.city = %s"
        params.append(city)
    elif role == "zone_admin":
        query += " AND providers.zone_id = %s"
        params.append(zone_id)
    cursor.execute(query, params)
    booking = cursor.fetchone()
    return render_template("admin/view_booking.html", booking=booking, zone_name=zone_name)



@admin.route("/admin/notifications")
def admin_notifications():
    if "admin_id" not in session:
        return redirect("/login")
    
    admin_id = session["admin_id"]
    role = session.get("role")       # city_admin or zone_amdmin

    cursor = connection.cursor(dictionary=True)
    query="""
        SELECT * FROM notifications
        WHERE receiver_id = %s AND receiver_type = %s
        ORDER BY created_at DESC
    """
    
    cursor.execute(query, (admin_id, role))
    notifications = cursor.fetchall()
    cursor.close()
    return render_template("admin/notifications.html", notifications=notifications)


#---------------- admin view pending providers verification----------------
@admin.route("/providers/pending")
def pending_providers():

    if "admin_id" not in session:
        return redirect("/login")
    
    role = session["role"]
    city = session["city"]
    zone_id = session.get("zone_id")

    cursor = connection.cursor(dictionary=True)
    #-----------------------------------------
    zone_name = None
    if session.get("zone_id"):
        cursor.execute("SELECT zone_name FROM zones WHERE zone_id = %s", (session["zone_id"], ))
        zone = cursor.fetchone()
        if zone:
            zone_name = zone["zone_name"]

    role = session["role"]
    city = session["city"]
    zone_id = session.get("zone_id")
#-----------------------------------
    query = """
            SELECT providers.*, services.service_name 
            FROM providers
            JOIN services ON providers.service_id = services.service_id
            WHERE verification_status = 'pending'
        """
    params = []
    if role == "city_admin":
        query += " AND providers.city = %s"
        params.append(city)
    elif role == "zone_admin":
        query += " AND providers.zone_id = %s"
        params.append(zone_id)
    
    cursor.execute(query, params)
    providers = cursor.fetchall()
    cursor.close()
    return render_template("admin/pending_providers.html", providers=providers, zone_name=zone_name)



#----------------admin approve provider---------------
@admin.route("/providers/approve/<int:provider_id>", methods=["POST"])
def approve_provider(provider_id):

    if "admin_id" not in session:
        return redirect("/login")
    role = session["role"]
    city = session["city"]
    zone_id = session.get("zone_id")
    admin_id = session["admin_id"]

    cursor = connection.cursor(dictionary=True)
    #-----------------------------------------
    zone_name = None
    if session.get("zone_id"):
        cursor.execute("SELECT zone_name FROM zones WHERE zone_id = %s", (session["zone_id"], ))
        zone = cursor.fetchone()
        if zone:
            zone_name = zone["zone_name"]

    role = session["role"]
    city = session["city"]
    zone_id = session.get("zone_id")
#-----------------------------------

    message = "Your account has been approved. You can now offer your services on our platform."

    cursor.execute("UPDATE providers SET verification_status = 'approved' WHERE provider_id = %s", (provider_id, ))
    
    cursor.execute("INSERT INTO notifications(receiver_id, sender_id, message, type, receiver_type) VALUES(%s, %s, %s, %s, %s)", (provider_id, admin_id, message, "verification", "provider"))
    connection.commit()
    return redirect("/admin/providers")


#-----------------admin rejected provider--------------
@admin.route("/providers/reject/<int:provider_id>", methods=["POST"])
def reject_provider(provider_id):
    if "admin_id" not in session:
        return redirect("/login")
    
    role = session["role"]
    zone_id = session.get("zone_id")
    admin_id = session["admin_id"]
    reason = request.form.get("reason")
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""UPDATE providers 
        SET verification_status = 'rejected', rejected_reason = %s
        WHERE provider_id = %s
    """, (reason, provider_id))

    message = f"Your account has been rejected.Reason: {reason}"
    
  

    #-------------insert notification----------------
    
    cursor.execute("INSERT INTO notifications(receiver_id, sender_id, message, type, receiver_type) VALUES(%s, %s, %s, %s, %s)", (provider_id, admin_id, message, "verification", "provider"))
    connection.commit()
    return redirect("/admin/providers")

#--------------------view all providers-----------------------

@admin.route("/admin/providers/view/<int:provider_id>", methods=["GET", "POST"])
def view_provider(provider_id):
    if "admin_id" not in session:
        return redirect("/login")
    
    cursor = connection.cursor(dictionary=True)

    # get customer details by ID
    cursor.execute("""
        SELECT p.*, s.service_name, z.zone_name
        FROM providers p
        JOIN services s
            ON p.service_id = s.service_id
        LEFT JOIN zones z 
            ON p.zone_id = z.zone_id
        WHERE provider_id = %s
    """, (provider_id,))

    provider = cursor.fetchone()
    cursor.close()

    return render_template("admin/provider_view.html", provider=provider)


#-------------------active and deactive providers---------------------

@admin.route("/admin/provider/activate/<int:provider_id>")
def activate_provider(provider_id):
    if "admin_id" not in session:
        return redirect("/login")
    role = session.get("role")
    city = session.get("city")
    zone_id = session.get("zone_id")
    
    cursor = connection.cursor(dictionary=True)
    admin_id = session["admin_id"]


    cursor.execute("UPDATE providers SET status='active' WHERE provider_id=%s", (provider_id, ))
    connection.commit()
    
    message = "Your account has been activated by admin"
    cursor.execute("""
           INSERT INTO notifications (receiver_id, sender_id, message, type, receiver_type)
           VALUES (%s, %s, %s, %s, %s)
    """, (provider_id, admin_id, message, "account_activate", "provider" ))

    return redirect("/admin/providers")


@admin.route("/admin/provider/deactivate/<int:provider_id>")
def deactivate_provider(provider_id):
    if "admin_id" not in session:
        return redirect("/login")
    zone_id = session.get("zone_id")
    cursor = connection.cursor(dictionary=True)
    #---get admin id grom session--
    admin_id = session["admin_id"]

    cursor.execute("UPDATE providers SET status='inactive' WHERE provider_id=%s", (provider_id, ))
    connection.commit()

    #---send notification to customer---
    message = "Your account has been deactivated by admin."

    cursor.execute("""
           INSERT INTO notifications (receiver_id, sender_id, message, type, receiver_type)
           VALUES (%s, %s, %s, %s, %s)
    """, (provider_id, admin_id, message, "account_deactivate", "provider" ))
    connection.commit()
    
    return redirect("/admin/providers")


#--------------------view all customers-----------------------
@admin.route("/admin/customers/view/<int:customer_id>", methods=["GET", "POST"])
def view_customers(customer_id):
    if "admin_id" not in session:
        return redirect("/login")
    
    cursor = connection.cursor(dictionary=True)

    # get customer details by ID
    cursor.execute("""
        SELECT c.*, z.zone_name
        FROM customers c
        LEFT JOIN zones z ON c.zone_id = z.zone_id
        WHERE c.id = %s
    """, (customer_id,))

    customer = cursor.fetchone()
    cursor.close()

    return render_template("admin/customer_view.html", customer=customer)

#-------------------active and deactive customer---------------------

@admin.route("/admin/customer/activate/<int:id>")
def activate_customer(id):
    if "admin_id" not in session:
        return redirect("/login")

    cursor = connection.cursor()
    admin_id = session["admin_id"]
    cursor.execute("UPDATE customers SET status='active' WHERE id=%s", (id, ))
    connection.commit()
    
    message = "Your account has been activated by admin"
    cursor.execute("""
           INSERT INTO notifications (receiver_id, sender_id, message, type, receiver_type)
           VALUES (%s, %s, %s, %s, %s)
    """, (id, admin_id, message, "account_activate", "customer" ))

    return redirect("/admin/customers")


@admin.route("/admin/customer/deactivate/<int:id>")
def deactivate_customer(id):
    if "admin_id" not in session:
        return redirect("/login")

    cursor = connection.cursor(dictionary=True)
    #---get admin id grom session--
    admin_id = session["admin_id"]

    cursor.execute("UPDATE customers SET status='inactive' WHERE id=%s", (id, ))
    connection.commit()

    #---send notification to customer---
    message = "Your account has been deactivated by admin."

    cursor.execute("""
           INSERT INTO notifications (receiver_id, sender_id, message, type, receiver_type)
           VALUES (%s, %s, %s, %s, %s)
    """, (id, admin_id, message, "account_deactivate", "customer" ))
    connection.commit()
    
    return redirect("/admin/customers")

#---------------------------view all reviews-----------------------

@admin.route("/admin/view_all_reviews")
def check_all_reviews():
    if "admin_id" not in session:
        return redirect("/login")
    
    role = session.get("role")
    city = session.get("city")
    zone_id = session.get("zone_id")

    cursor = connection.cursor(dictionary=True)
    #-----------------------------------------
    zone_name = None
    if session.get("zone_id"):
        cursor.execute("SELECT zone_name FROM zones WHERE zone_id = %s", (session["zone_id"], ))
        zone = cursor.fetchone()
        if zone:
            zone_name = zone["zone_name"]

    role = session["role"]
    city = session["city"]
    zone_id = session.get("zone_id")
#-----------------------------------
    #---------------------GET sedarch inputs----------
    provider_name = request.args.get("provider_name")
    provider_id = request.args.get("provider_id")

    query ="""
        SELECT r.review_id, r.rating, r.review, r.created_at,
            b.booking_id, b.booking_date,
            c.name AS customer_name,
            p.name AS provider_name,
            p.provider_id,
            s.service_name
        FROM reviews r
        JOIN bookings b
            ON r.booking_id = b.booking_id
        JOIN customers c
            ON r.customer_id = c.id
        JOIN providers p
            ON r.provider_id = p.provider_id
        JOIN services s
            ON p.service_id = s.service_id
        WHERE 1 = 1
    """
    params = []
    if role == "city_admin":
        query += " AND p.city = %s"
        params.append(city)
    elif role == "zone_admin":
        query += " AND p.zone_id = %s"
        params.append(zone_id)


    #--------------FILTER BY PROVIDERS NAME-------------
    if provider_name:
        query += " AND p.name LIKE %s"
        params.append(f"%{provider_name}%")

    #----------------FILTER BY PROVIDER ID--------------
    if provider_id:
        query += " AND p.provider_id LIKE %s"
        params.append(provider_id)

    query += " ORDER BY r.created_at DESC"

    cursor.execute(query, params)
    reviews = cursor.fetchall()
    return render_template("admin/check_reviews.html", reviews=reviews, provider_id=provider_id, provider_name=provider_name, zone_name=zone_name)


#---------------------view reviews---------------------------

@admin.route("/admin/view_review/<int:review_id>")
def view_review(review_id):
    if "admin_id" not in session:
        return redirect("/login")
    
    role = session.get("role")
    city = session.get("city")
    zone_id = session.get("zone_id")
    
    cursor = connection.cursor(dictionary=True)
    #-----------------------------------------
    zone_name = None
    if session.get("zone_id"):
        cursor.execute("SELECT zone_name FROM zones WHERE zone_id = %s", (session["zone_id"], ))
        zone = cursor.fetchone()
        if zone:
            zone_name = zone["zone_name"]

    role = session["role"]
    city = session["city"]
    zone_id = session.get("zone_id")
#-----------------------------------

    query = """
        SELECT r.*,
            b.booking_id, b.booking_date, b.status, b.booking_time, b.address,
            c.name AS customer_name,
            p.name AS provider_name,
            s.service_name
        FROM reviews r
        JOIN bookings b
            ON r.booking_id = b.booking_id
        JOIN customers c
            ON r.customer_id = c.id
        JOIN providers p
            ON r.provider_id = p.provider_id
        JOIN services s
            ON p.service_id = s.service_id
        WHERE r.review_id = %s        
    """
    params = [review_id]

    if role == "city_admin":
        query += " AND b.city = %s"
        params.append(city)
    elif role == "zone_admin":
        query += " AND b.zone_id = %s"
        params.append(zone_id)
    cursor.execute(query, params)
    review = cursor.fetchone()
    return render_template("admin/view_review.html", review=review, zone_name=zone_name)



#-------------------------admin reports --------------------------


@admin.route("/admin/reports")
def reports():
    if "admin_id" not in session:
        return redirect("/login")
    
    role = session.get("role")
    city = session.get("city")
    zone_id = session.get("zone_id")
    
    cursor = connection.cursor(dictionary=True)
    #-----------------------------------------
    zone_name = None
    if session.get("zone_id"):
        cursor.execute("SELECT zone_name FROM zones WHERE zone_id = %s", (session["zone_id"], ))
        zone = cursor.fetchone()
        if zone:
            zone_name = zone["zone_name"]

    role = session["role"]
    city = session["city"]
    zone_id = session.get("zone_id")
#-----------------------------------

    #---------------------filter-------------
    base_condition = " WHERE 1=1 "
    params = []
    if role == "city_admin":
        base_condition += " AND city = %s "
        params.append(city)

    elif role == "zone_admin":
        base_condition += " AND zone_id = %s "
        params.append(zone_id) 
   

    # ----total revenue generated------
    cursor.execute(f"""SELECT SUM(total_amount) AS total_revenue 
        FROM bookings {base_condition} AND  status = 'completed'
    """, params)
    total_revenue = cursor.fetchone()['total_revenue'] or 0


    #--------------------top service------------------------------

    condition = []
    params = []
    if role == "city_admin":
        condition.append ("b.city = %s")
        params.append(city)
    elif role == "zone_admin":
        condition.append ("b.zone_id = %s")
        params.append(zone_id)
    condition.append("b.status = 'completed'" )
    
    query = """
        SELECT s.service_name, SUM(b.total_amount) AS revenue
        FROM bookings b
        JOIN services s ON b.service_id = s.service_id
    """
        
    if condition:
        query += " WHERE " + " AND ".join(condition)
    query +="""
        GROUP BY b.service_id
        ORDER BY revenue DESC
        LIMIT 1
    """
    cursor.execute(query, params)
    top_service = cursor.fetchone()

    #---------------------------------------total bookings-----
    cursor.execute(f"""
        SELECT COUNT(*) AS total_bookings 
        FROM bookings 
        {base_condition}
    """, params)
    total_bookings = cursor.fetchone()["total_bookings"]

    #---------------------------active providers----------------------
    condition = []
    params = []

    role = session.get("role")
    city = session.get("city")
    zone_id = session.get("zone_id")

    if role == "city_admin":
        condition.append ("city = %s")
        params.append(city)

    elif role == "zone_admin":
        condition.append ("zone_id = %s")
        params.append(zone_id)

    query = """
       SELECT COUNT(*) AS active_providers
       FROM providers
       WHERE verification_status = 'approved' AND status = 'active'
    """
    if condition:
        query += " AND " + " AND ".join(condition)
    cursor.execute(query, params)
    active_providers = cursor.fetchone()["active_providers"]

    #--------most booking provider(top provider)------
    cursor.execute(f"""
        SELECT p.name, COUNT(*) AS total_bookings
        FROM bookings b
        JOIN providers p ON b.provider_id = p.provider_id
        {base_condition.replace('city', 'p.city').replace('zone_id', 'p.zone_id')}
        GROUP BY b.provider_id
        ORDER BY total_bookings DESC
        LIMIT 1
    """, params)
    most_booking_provider = cursor.fetchone()


    #-----------------top performer provider-------------
    cursor.execute(f"""
        SELECT P.provider_id, p.name,s.service_name, COUNT(b.booking_id) AS total_jobs,
        COALESCE(AVG(r.rating), 0) AS rating,
        COALESCE(SUM(b.total_amount), 0) AS earnings
        FROM providers p
        LEFT JOIN services s
           ON p.service_id = s.service_id
        LEFT JOIN bookings b 
           ON p.provider_id = b.provider_id AND b.status = 'completed'
        LEFT JOIN reviews r
           ON p.provider_id = r.provider_id
        {base_condition.replace('city', 'p.city').replace('zone_id', 'p.zone_id')}
        GROUP BY p.provider_id
        ORDER BY total_jobs DESC, rating DESC
        LIMIT 2
    """, params)
    top_performer_providers = cursor.fetchall()

    #----total customers------
    cursor.execute(f"""
        SELECT COUNT(*) AS total_customers 
        FROM customers
        {base_condition}
    """, params)
    total_customers = cursor.fetchone()["total_customers"]


    #---------------------momtly revenue ----------
    condition = []
    params = []
    if role == "city_admin":
        condition.append ("city = %s")
        params.append(city)
    elif role == "zone_admin":
        condition.append ("zone_id = %s")
        params.append(zone_id)
    condition.append("bookings.status = 'completed'" )

    limit = 1
    page = request.args.get('page', 1, type=int)
    offset = (page -1) * limit
    query = """
        SELECT DATE_FORMAT(booking_date, '%Y-%m') AS month, 
        SUM(total_amount) AS revenue,
        COUNT(booking_id) AS total_bookings,
        SUM(total_amount) AS earnings
        FROM bookings
    """
    if condition:
        query += " WHERE " + " AND ".join(condition)
    query += """
       GROUP BY month
       ORDER BY month DESC
       LIMIT %s OFFSET %s
    """
    cursor.execute(query, params + [limit, offset])
    monthly_revenue = cursor.fetchall()

    #--------new users per month-------  
    condition = []
    params = []

    role = session.get("role")
    city = session.get("city")
    zone_id = session.get("zone_id")

    if role == "city_admin":
        condition.append ("city = %s")
        params.append(city)

    elif role == "zone_admin":
        condition.append ("zone_id = %s")
        params.append(zone_id)
        #----current month filter----
    condition.append("DATE_FORMAT(created_at, '%Y-%m') = DATE_FORMAT(CURRENT_DATE(), '%Y-%m')")
    query = """
      SELECT COUNT(*) AS new_customers
      FROM customers
    """
    if condition:
        query += " WHERE " + " AND ".join(condition)
    cursor.execute(query, params)
    new_customers_per_month = cursor.fetchone()["new_customers"]

    cursor.close()
    return render_template("admin/admin_reports.html",
                            total_revenue=total_revenue,
                            top_service=top_service, total_bookings=total_bookings,page=page,zone_name=zone_name, 
                            active_providers=active_providers, total_customers=total_customers, new_customers_per_month=new_customers_per_month,
                            most_booking_provider=most_booking_provider, monthly_revenue=monthly_revenue, top_performer_providers=top_performer_providers)

   

@admin.route("/admin/reports/all_providers")
def all_providers_reports():
    if "admin_id" not in session:
        return redirect("/login")
    
    admin_id = session["admin_id"]
    cursor = connection.cursor(dictionary=True)
       #-----------------------------------------
    zone_name = None
    if session.get("zone_id"):
        cursor.execute("SELECT zone_name FROM zones WHERE zone_id = %s", (session["zone_id"], ))
        zone = cursor.fetchone()
        if zone:
            zone_name = zone["zone_name"]

    role = session["role"]
    city = session["city"]
    zone_id = session.get("zone_id")
#-----------------------------------
    page = request.args.get('page', 1, type = int)
    limit = 10
    offset = (page - 1) * limit

    cursor.execute("""
        SELECT P.provider_id, p.name,s.service_name, COUNT(b.booking_id) AS total_jobs,
        COALESCE(AVG(r.rating), 0) AS rating,
        COALESCE(SUM(b.total_amount), 0) AS earnings
        FROM providers p
        LEFT JOIN services s
           ON p.service_id = s.service_id
        LEFT JOIN bookings b 
           ON p.provider_id = b.provider_id AND b.status = 'completed'
        LEFT JOIN reviews r
           ON p.provider_id = r.provider_id
        WHERE p.city = %s
        GROUP BY p.provider_id, p.name, p.service_id, s.service_name
        ORDER BY total_jobs DESC, rating DESC
        LIMIT %s OFFSET %s
    """, (city, limit, offset))
    top_performer_providers = cursor.fetchall()
    return render_template("admin/all_providers_reports.html", top_performer_providers=top_performer_providers, page=page, zone_name=zone_name)
