from email import message

from flask import Flask, Blueprint, render_template, request, redirect, session
from config.database import connection
from utils.validations import *

provider = Blueprint("provider", __name__)


@provider.route("/provider/dashboard")
def provider_dashboard():
    if "provider_id" not in session:
        return redirect("/login")
    
    provider_id = session["provider_id"]
       
    user_name = session.get("provider_name")
    cursor = connection.cursor(dictionary=True)


    #----------total bookings-------------
    cursor.execute("SELECT COUNT(*) AS total FROM bookings WHERE provider_id = %s", (provider_id, ))
    total_jobs = cursor.fetchone()["total"]

    #-----------pending jobs--------
    cursor.execute("SELECT COUNT(*) AS total FROM  bookings WHERE provider_id = %s AND status = 'pending'", (provider_id, ))
    pending_jobs = cursor.fetchone()["total"]

    #-------completed jobs-----
    cursor.execute("SELECT COUNT(*) AS total FROM bookings WHERE provider_id = %s AND status = 'completed'", (provider_id, ))
    completed_jobs = cursor.fetchone()["total"]

    #-----------accepted jobs------------
    cursor.execute("SELECT COUNT(*) AS total FROM bookings WHERE provider_id = %s AND status = 'accepted'", (provider_id, ))
    accepted_jobs = cursor.fetchone()["total"]



    cursor.execute("SELECT COUNT(*) AS total FROM notifications WHERE receiver_id = %s AND is_read = FALSE", (provider_id,))
    result=cursor.fetchone()
    count = result["total"] if result else 0

    return render_template("/provider/dashboard.html", user_name=user_name, notification_count=count, total_jobs=total_jobs,
                           pending_jobs=pending_jobs, completed_jobs=completed_jobs, accepted_jobs=accepted_jobs)


@provider.route("/provider/my_jobs")
def my_jobs():
    if "provider_id" not in session:
        return redirect("/login")

    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT 
        bookings.booking_id,
        bookings.booking_date,
        bookings.status,
        customers.name AS customer_name,
        services.service_name
    FROM bookings
    JOIN customers ON bookings.customer_id = customers.id
    JOIN services ON bookings.service_id = services.service_id
    WHERE bookings.provider_id = %s
    ORDER BY bookings.booking_date DESC
    """
    
    cursor.execute(query, (session["provider_id"],))
    bookings = cursor.fetchall()

    return render_template("provider/my_jobs.html", bookings=bookings)


@provider.route("/accept_booking/<int:booking_id>", methods=["POST"])
def accept_booking(booking_id):

    if "provider_id" not in session:
        return redirect("/login")
    
    provider_id = session["provider_id"]

    cursor = connection.cursor(dictionary=True)

    query = "UPDATE bookings SET status = 'accepted' WHERE booking_id = %s"
    cursor.execute(query, (booking_id, ))

    # get customer_id
    cursor.execute("SELECT customer_id FROM bookings WHERE booking_id = %s", (booking_id,))
    booking = cursor.fetchone()
    customer_id = booking["customer_id"]

    message = "Your booking has been accpeted by the provider."

    cursor.execute("INSERT INTO notifications (receiver_id, sender_id,booking_id, message, type, receiver_type) VALUES (%s, %s, %s, %s, %s, %s)",  (customer_id, provider_id, booking_id, message, "accepted", "customer"))

    connection.commit()
    return redirect("/provider/my_jobs")

@provider.route("/reject_booking/<int:booking_id>", methods=["POST"])
def reject_booking(booking_id):

    if "provider_id" not in session:
        return redirect("/login")
    
    provider_id = session["provider_id"]

    reason = request.form["reason"]
    cursor = connection.cursor(dictionary=True)

    query="""
    UPDATE bookings
    SET status = 'cancelled', 
        cancelled_by = 'provider',
        cancel_reason = %s
    WHERE booking_id = %s
    """
    cursor.execute(query, (reason, booking_id))
    
    # get customer_id
    cursor.execute("SELECT customer_id FROM bookings WHERE booking_id = %s", (booking_id,))
    booking = cursor.fetchone()
    customer_id = booking["customer_id"]

    message = F"Your booking was rejected. Reason:{reason}"

    cursor.execute("INSERT INTO notifications (receiver_id, sender_id, booking_id, message, type, receiver_type) VALUES (%s, %s, %s, %s, %s, %s)", (customer_id, provider_id, booking_id, message, "rejected", "customer"))
    connection.commit()
    
    return redirect("/provider/my_jobs")


@provider.route("/complete_booking/<int:booking_id>", methods=["POST"])
def complete_booking(booking_id):

    if "provider_id" not in session:
        return redirect("/login")
    
    provider_id = session["provider_id"]

    cursor = connection.cursor(dictionary=True)

    query = "UPDATE bookings SET status = 'completed' WHERE booking_id = %s AND status = 'accepted'"
    cursor.execute(query, (booking_id, ))

    # get customer_id
    cursor.execute("SELECT customer_id FROM bookings WHERE booking_id = %s", (booking_id,))
    booking = cursor.fetchone()
    customer_id = booking["customer_id"]

    message = "Your booking work has been finished."

    cursor.execute("INSERT INTO notifications (receiver_id, sender_id,booking_id, message, type, receiver_type) VALUES (%s, %s, %s, %s, %s, %s)",  (customer_id, provider_id, booking_id, message, "completed", "customer"))

    connection.commit()
    return redirect("/provider/my_jobs")


@provider.route("/provider/notifications")
def provider_notifications():
    if "provider_id" not in session:
        return redirect("/login")
    
    provider_id = session["provider_id"]
    cursor = connection.cursor(dictionary=True)
    query="""
        SELECT * FROM notifications
        WHERE receiver_id = %s AND receiver_type = 'provider'
        ORDER BY created_at DESC
    """
    
    cursor.execute(query, (provider_id,))
    notifications = cursor.fetchall()
    return render_template("provider/notifications.html", notifications=notifications)

@provider.route("/provider/profile")
def provider_profile():
    if "provider_id" not in session:
        return redirect("/login")
    
    provider_id = session["provider_id"]
    cursor = connection.cursor(dictionary=True)
    zone_name = None
    if session.get("zone_id"):
        cursor.execute("SELECT zone_name FROM zones WHERE zone_id = %s", (session["zone_id"], ))
        zone = cursor.fetchone()
        if zone:
            zone_name = zone["zone_name"]
    zone_id = session.get("zone_id")
    cursor.execute("""
        SELECT p.*, s.service_name, zones.zone_name
        FROM providers p
        JOIN services s 
            ON p.service_id = s.service_id 
        LEFT JOIN zones
            ON p.zone_id = zones.zone_id        
        WHERE provider_id = %s""", (provider_id, ))
    provider = cursor.fetchone()

    return render_template("provider/profile.html", provider=provider, zone_name=zone_name)


@provider.route("/provider/available/<int:provider_id>")
def activate_provider(provider_id):
    if "provider_id" not in session:
        return redirect("/login")

    cursor = connection.cursor()
    cursor.execute("UPDATE providers SET provider_status='available' WHERE provider_id=%s", (provider_id, ))
    connection.commit()

    return redirect("/provider/profile")


@provider.route("/provider/unavailable/<int:provider_id>")
def deactivate_provider(provider_id):
    if "provider_id" not in session:
        return redirect("/login")

    cursor = connection.cursor()
    cursor.execute("UPDATE providers SET provider_status='unavailable' WHERE provider_id=%s", (provider_id,))
    connection.commit()

    return redirect("/provider/profile")



@provider.route("/provider/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if "provider_id" not in session:
        return redirect("/login")
    
    provider_id  = session["provider_id"]
    cursor = connection.cursor(dictionary=True)
    
    if request.method == "POST":
        email = request.form["email"]
        mobile = request.form["mobile"]
        city = request.form["city"]

        query = """
            UPDATE providers
            SET email=%s, mobile=%s, city=%s
            WHERE provider_id=%s
            """
        cursor.execute(query, (email, mobile, city, provider_id))
        connection.commit()

        return redirect("/provider/profile") 
    
    cursor.execute("SELECT * FROM providers WHERE provider_id = %s", (provider_id, ))
    provider = cursor.fetchone()

    return render_template("provider/edit_profile.html", provider=provider)


@provider.route("/provider/change_password", methods = ["GET", "POST"])
def change_password():
    if "provider_id" not in session:
        return redirect("/login")
    
    provider_id = session["provider_id"]
    cursor = connection.cursor(dictionary=True)

    
    error = ""
    success = ""

    if request.method=="POST":
        current_password= request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        cursor.execute("SELECT password from customers WHERE customer_id = %s", (provider_id, ))
        provider = cursor.fetchone()

        if provider["password"] != current_password:
            error = "current password is incorrect"

        #-----check new and confirm password match---------
        elif new_password != confirm_password:
            error = "New password and confirm password do not match"

        elif new_password == current_password:
            error = "New password cannot be same as current password"

        else:
            cursor.execute("UPDATE providerss SET password= %s WHERE provider_id =%s", (new_password, provider_id))
            connection.commit()
            success = "Password updated successfully"
            return redirect("/provider/profile")
        
    return render_template("/provider/change_password.html", error=error, success=success)

@provider.route("/provider/verification", methods=["GET", "POST"])
def provider_verification():
    dob_error = ""
    adhar_error = ""
    pan_error = ""
    bank_error = ""
    ifsc_error = ""
    description_error =  ""
    msg = ""
    message = ""

    dod = ""
    bank_account = ""
    ifsc_code = ""
    adhar = ""
    pan = ""
    description = ""
    if "provider_id" not in session:
        return redirect("/login")
    
    provider_id = session["provider_id"]
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT verification_status, rejected_reason, city, zone_id FROM providers WHERE provider_id = %s
    """, (provider_id, ))
    data = cursor.fetchone()

    if data:
        verification_status = data.get("verification_status", "not_submitted")
        rejected_reason = data.get("rejected_reason", "")
        city = data.get("city", "")
        zone_id = data.get("zone_id")
    else:
        verification_status = "not_submitted"
        rejected_reason = ""
        city = None
        zone_id = None
 
    if request.method == "POST":
        dob = request.form["dob"]
        bank_account = request.form["bank_account"]
        ifsc_code = request.form["ifsc_code"]
        adhar =  request.form["adhar"]
        pan = request.form["pan"]
        description = request.form["description"]

        if dob== "":
            dob_error = "Date of birth required"

        if adhar =="":
            adhar_error = "Aadhar required"
        elif not is_valid_aadhar(adhar):
            adhar_error = "Adhar must be 12 digits"

        if pan =="":
            pan_error = "PAN required"
        elif not is_valid_pan(pan):
            pan_error = "Invalid PAN format"

        if bank_account == "":
            bank_error = "Bank account required"
        elif not is_valid_bank_account(bank_account):
            bank_error = "Invalid account number"

        if ifsc_code == "":
            ifsc_error = "IFSC required"
        elif not is_valid_ifsc(ifsc_code):
            ifsc_error = "Invalid IFSC code"

        if description =="":
            description_error = "description required"
        
        #-----------check duplicate adhar----------------
        cursor.execute("SELECT provider_id FROM providers WHERE adhar = %s AND provider_id !=%s", (adhar, provider_id))
        exists_error = cursor.fetchone()
        if exists_error:
            adhar_error = "Aadhar already exists"

        #-------------check duplicate pan-----------------
        cursor.execute("SELECT provider_id FROM providers WHERE pan = %s AND provider_id !=%s", (pan, provider_id))
        exists_error = cursor.fetchone()
        if exists_error:
            pan_error = "PAN already exists"

        #----------final check----
        if dob_error =="" and adhar_error =="" and pan_error=="" and bank_error =="" and ifsc_error == "" and description_error == "":

            cursor.execute("""
                UPDATE providers SET dob =%s, bank_account = %s, ifsc_code =%s, adhar =%s, pan =%s, description = %s, verification_status = 'pending'
                WHERE provider_id = %s
            """, (dob, bank_account, ifsc_code, adhar, pan, description, provider_id))

            cursor.execute("SELECT admin_id FROM admins WHERE city = %s", (city, ))
            admin = cursor.fetchone()
            admin_id = admin["admin_id"] if admin else None


            if verification_status == "pending":
                msg = "Already submitted. Please Wait for admin approval"
            elif verification_status == "approved":
                message = "Already verified. Cannot resubmit"
            else:
                msg = "Verification details submitted successfully."

            receiver_id = None
            receiver_type = None

            #----------if provider has zone-----
            if zone_id:
                cursor.execute("""
                   SELECT admin_id
                   FROM admins
                   WHERE zone_id  = %s AND status = 'active'
                """, (zone_id, ))
                zone_admin = cursor.fetchone()

                if zone_admin:
                    receiver_id = zone_admin["admin_id"]
                    receiver_type = "zone_admin"

            if not receiver_id:
                cursor.execute("""
                    SELECT admin_id
                    FROM admins
                    WHERE city = %s AND zone_id IS NULL AND status = 'active'
                """, (city, ))
                city_admin = cursor.fetchone()
                if city_admin:
                    receiver_id = city_admin["admin_id"]
                    receiver_type = "city_admin"

            if receiver_id:
                message = f"New provider verification request from provider ID {provider_id}"

                cursor.execute("""  
                    INSERT INTO notifications (receiver_id, sender_id, message, type, receiver_type)
                    VALUES (%s, %s, %s, %s, %s)
                """, (receiver_id, provider_id, message, "verification", receiver_type))
                connection.commit()
          
    return render_template("provider/verification.html", verification_status=verification_status, rejected_reason=rejected_reason,msg=msg, 
                           dob_error=dob_error, adhar_error=adhar_error, pan_error=pan_error, bank_error=bank_error, ifsc_error=ifsc_error,
                           dod=dod, bank_account=bank_account, ifsc_code=ifsc_code, adhar=adhar, pan=pan, description=description, message=message)


@provider.route("/provider/bookings/view/<int:booking_id>")
def view_booking(booking_id):
    if "provider_id" not in session:
        return redirect("/login")
    
    provider_id = session["provider_id"]
    cursor = connection.cursor(dictionary=True)
    cursor = connection.cursor(dictionary=True)
       #-----------------------------------------
    zone_name = None
    if session.get("zone_id"):
        cursor.execute("SELECT zone_name FROM zones WHERE zone_id = %s", (session["zone_id"], ))
        zone = cursor.fetchone()
        if zone:
            zone_name = zone["zone_name"]

   
    zone_id = session.get("zone_id")

    cursor.execute("""
        SELECT
            bookings.*,
            customers.name AS customer_name,
            providers.name AS provider_name,
            services.service_name,
            zones.zone_name,
            reviews.rating,
            reviews.review
        FROM bookings
        JOIN customers ON bookings.customer_id = customers.id
        JOIN providers ON bookings.provider_id = providers.provider_id
        JOIN services ON bookings.service_id = services.service_id
        LEFT JOIN reviews ON bookings.booking_id = reviews.booking_id
        LEFT JOIN zones
            ON bookings.zone_id = zones.zone_id
        WHERE bookings.booking_id = %s""", (booking_id, ))
    
    booking = cursor.fetchone()
    return render_template("provider/view_bookings.html", booking=booking,zone_name=zone_name)


@provider.route("/providers/view_reviews")
def view_review():
    if "provider_id" not in session:
        return redirect("/login")
    
    provider_id = session["provider_id"]
    cursor = connection.cursor(dictionary=True)
    

    cursor.execute("""
       SELECT r.*, c.name AS customer_name, p.name AS provider_name, b.booking_date
       FROM reviews r
       JOIN customers c
            ON r.customer_id = c.id
       JOIN providers p
            ON r.provider_id = p.provider_id
       JOIN bookings b
            ON r.booking_id = b.booking_id
        WHERE r.provider_id = %s
        ORDER BY r.created_at DESC
    """, (provider_id, ))

    reviews = cursor.fetchall()
    return render_template("provider/view_reviews.html", reviews=reviews)