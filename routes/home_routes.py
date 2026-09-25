from flask import Flask, Blueprint, render_template, request, redirect, session
from config.database import connection
from utils.validations import *



home = Blueprint("home", __name__)


@home.route("/home_page")
def home_page():
    if "role" not in session or session["role"] != "customer":
        return redirect ("/login")

    cursor = connection.cursor(dictionary=True)
    cursor.execute("""SELECT * 
        FROM services 
        WHERE status = 'available'
    """)

    services = cursor.fetchall()
    cursor.close()

    return render_template("home_page.html", services=services)

@home.route("/search")
def search():
    keyword = request.args.get("search")
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM services WHERE service_name LIKE %s AND status = 'available'", ('%'+ keyword + '%',))
    services = cursor.fetchall()

    return render_template("home_page.html", services=services)


@home.route("/servicers", methods=['GET', 'POST'])
def servicers():
    service_id = request.args.get("service_id")

    price = request.args.get("price", "")
    rating = request.args.get("rating", "")
    experience = request.args.get("experience", "")
    city = request.args.get("city", "")
    search = request.args.get("search", "")


    query = """
    SELECT
        providers.provider_id,
        providers.name,
        services.service_name,
        services.service_id,
        providers.price,
        providers.provider_status,
        providers.inclusions,
        providers.verification_status,
        
        COUNT(reviews.review_id) AS reviews_count,
        IFNULL(AVG(reviews.rating), 0) AS avg_rating
    FROM providers
    JOIN services 
        ON providers.service_id = services.service_id
    LEFT JOIN reviews
        ON providers.provider_id = reviews.provider_id
    WHERE providers.provider_status='available' AND providers.verification_status= 'approved'
    
    """
    values=[]

    if service_id:
        query += " AND providers.service_id = %s"
        values.append (service_id)

    if search:
        query += " AND (services.service_name LIKE %s OR providers.name LIKE %s)"
        values.append(f"%{search}%")
        values.append(f"%{search}%")

    if city:
        query += " AND LOWER(providers.city LIKE %s)"
        values.append(f"%{city}%")

    if price:
        query += " AND price <= %s"   
        values.append(price)

    if rating:
        query += " AND rating >= %s"
        values.append(rating)
    
    if experience:
        query += " AND experience >= %s"
        values.append(experience)
        
    query += "GROUP BY providers.provider_id"

    cursor = connection.cursor(dictionary=True)
    cursor.execute(query, values)
    providers = cursor.fetchall()
    cursor.close()

    return render_template(
        "servicers.html", providers=providers, price=price, city=city,
        rating=rating, experience=experience, search=search, service_id=service_id
    )


@home.route("/booking/<int:provider_id>/<int:service_id>", methods = ["GET", "POST"])
def booking(provider_id, service_id):

    if "user_id" not in session:
        return redirect("/login")
    
    customer_id = session["user_id"]


    date_error = ""
    time_error = ""
    address_error = ""
    city_error = ""
    date = ""
    time = ""

    #---------------------TIME SLOTS---------------------------
    all_slots = [
        "09:00","10:00", 
        "11:00", "12:00",
        "14:00", "15:00",
        "16:00", "17:00"
        ]
    
    cursor = connection.cursor(dictionary=True)

    #--------get zones--------
    cursor.execute("SELECT zone_id, zone_name FROM zones")
    zones = cursor.fetchall()

    #----------Get booked slots(available slots)-----
    selected_date = request.form.get("date") if request.method == "POST" else None
    available_slots = all_slots.copy()


    if selected_date:
        cursor.execute("""
            SELECT booking_time
            FROM bookings
            WHERE provider_id = %s
            AND booking_date = %s
            AND status IN ('pending', 'accepted')
        """, (provider_id, selected_date))
        booked = cursor.fetchall()

        booked_times = [str(row["booking_time"]) [:5] for row in booked]

        available_slots=[slot for slot in all_slots if slot not in booked_times]
    

    if request.method == "POST":
        
        date = request.form['date']
        time = request.form['time']
        city = request.form['city']
        zone_id = request.form["zone_id"]
        address = request.form['address']

        #date validation
        if date == "":
            date_error = "Date is required"
        elif not is_valid_date(date):
            date_error = "Past date not allowed"

        #time validation
        if time == "":
            time_error = "Time is required"

        #city valildation
        if city == "":
            city_error = "City is required"

        if zone_id == "":
            zone_id =None


        #----------address valildation------------
        if address == "":
            address_error = "Address is required"
        elif not is_valid_address(address):
            address_error = "Address must be at least 5 charachters"

        if date_error =="" and time_error == "" and address_error == "" and city_error =="":

#----------- customer same time check booking limt------------------
            cursor.execute("""
               SELECT COUNT(*) AS count
               FROM bookings
               WHERE customer_id  = %s
               AND booking_date = %s                 #(customer cannot book multple providers at same time)
               AND booking_time = %s                  
               AND status IN ('pending', 'accepted')
            """, (customer_id, date, time))
            result = cursor.fetchone()

            if result["count"] > 0:
                return "You already have a booking at this time"
            
#-----------provider double booking check-------------
            cursor.execute("""
               SELECT COUNT(*) AS count
               FROM bookings
               WHERE provider_id  = %s
               AND booking_date = %s                 
               AND booking_time = %s                  
               AND status IN ('pending', 'accepted')
            """, (provider_id, date, time))
            result = cursor.fetchone()

            if result["count"] > 0:
                return "This provider is already booked at this time"
            
#---------------limit per day--(maximun 3 bookings)---------------
            cursor.execute("""
               SELECT COUNT(*) AS count
               FROM bookings
               WHERE customer_id  = %s
               AND booking_date = %s
               AND status IN ('pending', 'accepted')
            """, (customer_id, date))
            day_result = cursor.fetchone()

            if day_result["count"] >=3:
                return "Maximun 3 bookings allowed per day"
            
 #--------------if all are check pass insert booking-----------
            query = """INSERT INTO bookings(customer_id, provider_id, service_id, booking_date, booking_time, city, zone_id, address)
            VALUES(%s, %s, %s, %s, %s,  %s, %s, %s)"""
            values= (customer_id, provider_id, service_id, date, time, city, zone_id, address)
            cursor.execute(query, values)
            booking_id = cursor.lastrowid

            message = f"New booking request from Customer {customer_id}"

            cursor.execute("""
                INSERT INTO notifications(receiver_id, sender_id, booking_id, message, type, receiver_type) 
                           VALUES (%s, %s, %s, %s, %s, %s)""",(provider_id, customer_id, booking_id, message, "booking_request", "provider"))
            connection.commit()
            return "Booking Successful"
    return render_template("booking.html", provider_id=provider_id, date_error=date_error,service_id = service_id,zones=zones, 
                           date = date, time = time,slots = available_slots, time_error=time_error, address_error=address_error, city_error=city_error)


#--------------provider profile--------------
@home.route("/profile/<int:provider_id>")
def provider_profile(provider_id):

    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT providers.*, services.service_name
        FROM providers
        JOIN services ON providers.service_id = services.service_id
        WHERE provider_id=%s""", (provider_id,))

    provider = cursor.fetchone()

    return render_template("provider_profile.html", provider=provider)

@home.route("/providers/check_reviews/<int:provider_id>")
def check_review(provider_id):
    if "user_id" not in session:
        return redirect("/login")
    
    customer_id = session["user_id"]
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
    return render_template("customer/check_reviews.html", reviews=reviews)
