from flask import Flask, Blueprint, render_template, request, redirect, session
from config.database import connection
from utils.validations import *

customer = Blueprint("customer", __name__)


@customer.route("/dashboard")
def user_dashboard():
    if "user_id" not in session:
        return redirect("/login")
    
    customer_id = session["user_id"]
    user_name = session.get("customer_name")
    cursor = connection.cursor(dictionary=True)

    #-----------------Completed bookings-----------------------
    cursor.execute("""
        SELECT COUNT(*) AS total_bookings
        FROM bookings
        WHERE customer_id = %s AND status = 'completed'
    """, (customer_id, ))
    completed = cursor.fetchone()["total_bookings"]

    #--------------pending bookings-------------------
    cursor.execute("""
        SELECT COUNT(* ) AS pending_bookings
        FROM bookings
        WHERE customer_id = %s AND status = 'pending'
        """,(customer_id, ))
    pending_bookings = cursor.fetchone()["pending_bookings"]

    #-----------------recent bookings----------------------
    cursor.execute("""
        SELECT 
        bookings.booking_id,
        bookings.booking_date,
        bookings.status,
        services.service_name
    FROM bookings 
    JOIN services
        ON bookings.service_id = services.service_id
    WHERE bookings.customer_id = %s
    ORDER BY bookings.booking_date DESC
    LIMIT 3
    """, (customer_id, ))
    bookings = cursor.fetchall()

    cursor.close()
    return render_template("/customer/dashboard.html", user_name=user_name, completed=completed, pending_bookings=pending_bookings, bookings=bookings)


@customer.route("/my_bookings")
def my_bookings():
    if "user_id" not in session:
        return redirect("/login")
    
    customer_id = session["user_id"]
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT 
        bookings.booking_id,
        bookings.booking_date,
        bookings.status,
        services.service_name,
        p.name AS provider_name
    FROM bookings 
    JOIN services
        ON bookings.service_id = services.service_id
    LEFT JOIN providers p
        ON bookings.provider_id = p.provider_id
    LEFT JOIN reviews r 
        ON bookings.booking_id = r.booking_id
    WHERE bookings.customer_id = %s
    ORDER BY bookings.booking_date DESC
    """

    cursor.execute(query, (session['user_id'],))
    bookings = cursor.fetchall()

    cursor.close()

    return render_template("customer/my_bookings.html", bookings=bookings)


#-------------------------------reschedule--------------------------------

@customer.route("/reschedule/<int:booking_id>", methods = ["GET", "POST"])
def reschedule(booking_id):
    if "user_id" not in session:
        return redirect("/login")
    
    customer_id = session["user_id"]
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM bookings WHERE booking_id = %s
    """, (booking_id, ))
    booking = cursor.fetchone()


    if request.method == "POST":
        new_date = request.form["date"]

        cursor = connection.cursor()
        cursor.execute("""
            UPDATE bookings
            SET booking_date = %s, status = "pending"
            WHERE booking_id = %s""", (new_date, booking_id))
        
        message = f"Booking #{booking_id} rescheduled to {new_date}"

        cursor.execute("""
           INSERT INTO notifications (receiver_id, sender_id, booking_id, message, type, receiver_type)
           VALUES (%s, %s, %s, %s, %s, %s)
        """, (booking["provider_id"], booking["customer_id"], booking_id, message, "booking_reschedule", "provider" ))
        connection.commit()
        cursor.close()
    return render_template("/booking.html", booking_id=booking_id)

#-----------------cancelled ------------------------

@customer.route("/cancel/<int:booking_id>", methods=["GET", "POST"])
def cancel_booking(booking_id):

    if "user_id" not in session:
        return redirect("/login")
    
    customer_id = session["user_id"]
    cursor = connection.cursor(dictionary=True)
    

    # Get booking
    cursor.execute("""
        SELECT * FROM bookings 
        WHERE booking_id = %s AND customer_id = %s
    """, (booking_id, session["user_id"]))

    booking = cursor.fetchone()

    if not booking:
        return "Invalid booking"


    if booking["status"] != "pending":
        return "Only pending bookings can be cancelled"

    if request.method == "POST":
        reason = request.form.get("reason")
        custom_reason = request.form.get("custom_reason", "").strip()

        if not reason:
            return "Please select a reason"

        if reason == "other" and not custom_reason:
            return "Please enter custom reason"

        final_reason = custom_reason if reason == "other" else reason

        provider_id = booking["provider_id"]
        customer_id = booking["customer_id"]

        cursor.execute("""
            UPDATE bookings 
            SET status = 'cancelled',
                cancel_reason = %s,
                cancelled_by = 'customer'
            WHERE booking_id = %s
        """, (final_reason, booking_id))

        message = f"Booking #{booking_id} Cancelled by customer.Reason:{final_reason} "

        cursor.execute("""
           INSERT INTO notifications (receiver_id, sender_id, booking_id, message, type, receiver_type)
           VALUES (%s, %s, %s, %s, %s, %s)
        """, (provider_id, customer_id, booking_id, message, "booking_cancelled", "provider" ))

        connection.commit()

        return redirect("/my_bookings")

    return render_template("/customer/cancel_booking.html", booking_id=booking_id)

@customer.route("/notifications")
def notifications():

    
    if "user_id" not in session:
        return redirect("/login")
    
    customer_id = session["user_id"]
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
                SELECT * FROM notifications
                WHERE receiver_id = %s AND receiver_type = 'customer'
                ORDER BY created_at DESC""", (session["user_id"],))

    notifications= cursor.fetchall()
    
    cursor.execute("""
                   UPDATE notifications
                   SET is_read = TRUE
                   WHERE receiver_id = %s AND receiver_type = 'customer'
                   """, (customer_id, ))
    connection.commit()

    return render_template("customer/notifications.html", notifications=notifications)


#--------------------customer profile----------------

@customer.route("/customer/profile")
def customer_profile():
    if "user_id" not in session:
        return redirect("/login")
    
    customer_id = session["user_id"]
    cursor = connection.cursor(dictionary=True)
     #-----------------------------------------
    zone_name = None
    if session.get("zone_id"):
        cursor.execute("SELECT zone_name FROM zones WHERE zone_id = %s", (session["zone_id"], ))
        zone = cursor.fetchone()
        if zone:
            zone_name = zone["zone_name"]

    city = session["city"]
    zone_id = session.get("zone_id")

    cursor.execute("""
            SELECT customers.*, zones.zone_name
            FROM customers
            LEFT JOIN zones 
                ON customers.zone_id = zones.zone_id
             WHERE customers.id = %s
    """, (customer_id, ))
    customer = cursor.fetchone()

    return render_template("customer/profile.html", customer=customer, zone_name=zone_name)

@customer.route("/customer/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if "user_id" not in session:
        return redirect("/login")
    
    customer_id = session["user_id"]
    cursor = connection.cursor(dictionary=True)
    
    if request.method == "POST":
        email = request.form["email"]
        mobile = request.form["mobile"]
        city = request.form["city"]

        query = """
            UPDATE customers
            SET email=%s, mobile=%s, city=%s
            WHERE id=%s
            """
        cursor.execute(query, (email, mobile, city, customer_id, ))
        connection.commit()

        return redirect("/customer/profile") 
    
    cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id, ))
    customer = cursor.fetchone()

    return render_template("customer/edit_profile.html", customer=customer)


@customer.route("/customer/change_password", methods = ["GET", "POST"])
def change_password():
    if "user_id" not in session:
        return redirect("/login")
    
    customer_id = session["user_id"]
    cursor = connection.cursor(dictionary=True)

    error = ""
    success = ""

    if request.method=="POST":
        current_password= request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        cursor.execute("SELECT password from customers WHERE customer_id = %s", (customer_id, ))
        customer = cursor.fetchone()

        if customer["password"] != current_password:
            error = "current password is incorrect"

        #-----check new and confirm password match---------
        elif new_password != confirm_password:
            error = "New password and confirm password do not match"

        elif new_password == current_password:
            error = "New password cannot be same as current password"

        else:
            cursor.execute("UPDATE customers SET password= %s WHERE customer_id =%s", (new_password, customer_id))
            connection.commit()
            success = "Password updated successfully"
            return redirect("/customer/profile")
        
    return render_template("/customer/change_password.html", error=error, success=success)

#------------------------------view booking details and add reviews-----------

@customer.route("/customer/bookings/view/<int:booking_id>")
def view_booking(booking_id):
    if "user_id" not in session:
        return redirect("/login")
    
    customer_id = session["user_id"]
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
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
        WHERE bookings.booking_id = %s""", (booking_id, ))
    
    booking = cursor.fetchone()
    return render_template("customer/view_booking.html", booking=booking)

    #-------------------Reviews--------------------------

@customer.route("/customer/add_reviews/<int:booking_id>", methods=["GET", "POST"])
def add_reviews(booking_id):
    if "user_id" not in session:
        return redirect("/login")
    
    customer_id = session["user_id"]
    cursor = connection.cursor(dictionary=True)

    #-----------get booking details-----------
    cursor.execute("""
        SELECT provider_id, status FROM bookings
        WHERE booking_id = %s AND customer_id = %s
    """, (booking_id, customer_id))
    booking = cursor.fetchone()

    if not booking:
        return "Invalid booking"
    
    #----not completed------
    if booking["status"] != "completed":
        return "Only completed bookings can be reviewed"
    #----check if review already exists--------
    cursor.execute("""
        SELECT * FROM reviews
        WHERE booking_id = %s AND customer_id = %s
    """, (booking_id, customer_id))
    review = cursor.fetchone()

    if review:
        return "Review already exists for this booking"
    
    if request.method == "POST":
        rating = request.form["rating"]
        review = request.form["review"]

        cursor.execute("""
            INSERT INTO reviews (booking_id, provider_id, customer_id, rating, review)
            VALUES (%s, %s, %s, %s, %s)
        """, (booking_id, booking["provider_id"],customer_id, rating, review))
        connection.commit()

        return redirect("/my_bookings")
    return render_template("/customer/reviews.html", booking_id=booking_id)


@customer.route("/view_review/<int:booking_id>")
def view_review(booking_id):
    if "user_id" not in session:
        return redirect("/login")
    
    customer_id = session["user_id"]
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
       SELECT r.rating, r.review, p.name AS provider_name
       FROM reviews r
       JOIN providers p 
            ON r.provider_id = p.provider_id
        WHERE r.booking_id = %s
    """, (booking_id, ))

    review = cursor.fetchone()
    return render_template("customer/view_booking.html", review=review)
