from flask import Flask, render_template, request, redirect, session
from datetime import datetime
import sqlite3
import json
import webbrowser

app = Flask(__name__)
app.secret_key = "foodoraa"


# ================= DATABASE =================

def init_db():

    conn = sqlite3.connect('database.db')

    cur = conn.cursor()

    # DONATIONS TABLE

    cur.execute("""

    CREATE TABLE IF NOT EXISTS donations(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        food TEXT,

        quantity TEXT,

        people TEXT,

        location TEXT,

        vehicle TEXT,

        distance INTEGER,

        delivery_fee INTEGER,

        status TEXT DEFAULT 'Pending'

    )

    """)

    # DELIVERIES TABLE

    cur.execute("""

    CREATE TABLE IF NOT EXISTS deliveries(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        food TEXT,

        volunteer TEXT,

        location TEXT,

        status TEXT

    )

    """)

    # SAVINGS TABLE

    cur.execute("""

    CREATE TABLE IF NOT EXISTS savings(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        amount INTEGER,

        details TEXT,

        vehicle TEXT,

        distance INTEGER,

        datetime TEXT

    )

    """)

    conn.commit()
    conn.close()


init_db()


# ================= HOME =================

@app.route('/')
def home():

    return render_template('index.html')


# ================= ABOUT =================

@app.route('/about')
def about():

    return render_template('about.html')


# ================= ADMIN LOGIN =================

@app.route('/admin_login')
def admin_login():

    return render_template('admin_login.html')


# ================= LOGIN =================

@app.route('/login', methods=['GET', 'POST'])

def login():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        if username and password:

            session['user'] = username

            return redirect('/')

    return render_template('login.html')


# ================= LOGOUT =================

@app.route('/logout')

def logout():

    session.clear()

    return redirect('/signin')


# ================= SIGNIN =================

@app.route('/signin')

def signin():

    return render_template('signin.html')


# ================= SIGNUP =================

@app.route('/signup')

def signup():

    return render_template('signup.html')


# ================= OTP =================

@app.route('/otp')

def otp():

    return render_template('otp.html')


# ================= VERIFY OTP =================

@app.route('/verify_otp', methods=['POST'])

def verify_otp():

    otp = request.form['otp']

    if otp == "0454":

        return redirect('/userinfo')

    else:

        return '''

        <h1 style="color:red;text-align:center;">

        Wrong OTP ❌

        </h1>

        '''


# ================= GOOGLE LOGIN =================

@app.route('/google')

def google():

    return render_template('google.html')


# ================= USER INFO =================

@app.route('/userinfo')

def userinfo():

    return render_template('userinfo.html')


# ================= DONATE =================

@app.route('/donate', methods=['GET', 'POST'])

def donate():

    if request.method == 'POST':

        food = request.form['food']

        quantity = request.form['quantity']

        people = request.form['people']

        location = request.form['location']

        vehicle = request.form.get("vehicle")

        distance = int(request.form.get("distance"))

        # DELIVERY RATE

        rate = 0

        if vehicle == "bike":

            rate = 10

        elif vehicle == "auto":

            rate = 20

        elif vehicle == "tempo":

            rate = 30

        # FINAL DELIVERY FEE

        delivery_fee = distance * rate

        conn = sqlite3.connect('database.db')

        cur = conn.cursor()

        cur.execute("""

        INSERT INTO donations(

            food,

            quantity,

            people,

            location,

            vehicle,

            distance,

            delivery_fee,

            status

        )

        VALUES(?,?,?,?,?,?,?,?)

        """, (

            food,

            quantity,

            people,

            location,

            vehicle,

            distance,

            delivery_fee,

            'Pending'

        ))

        conn.commit()

        conn.close()

        return redirect('/')

    return render_template('donate.html')


# ================= ACCEPT =================

@app.route('/accept/<int:id>')

def accept(id):

    conn = sqlite3.connect('database.db')

    cur = conn.cursor()

    cur.execute("SELECT * FROM donations WHERE id=?", (id,))

    order = cur.fetchone()

    location = ""

    if order:

        food = order[1]

        location = order[4]

        cur.execute("""

        INSERT INTO deliveries(

            food,

            volunteer,

            location,

            status

        )

        VALUES(?,?,?,?)

        """, (

            food,

            "Volunteer",

            location,

            "Accepted"

        ))

        conn.commit()

    conn.close()

    return redirect(

        "https://www.google.com/maps/search/" + location

    )


# ================= ACCEPT DELIVERY =================

@app.route('/accept_delivery/<int:id>')

def accept_delivery(id):

    conn = sqlite3.connect('database.db')

    cur = conn.cursor()

    # GET ORDER DETAILS

    cur.execute("""

    SELECT delivery_fee, vehicle, distance

    FROM donations

    WHERE id=?

    """, (id,))

    result = cur.fetchone()

    delivery_fee = 0

    vehicle = ""

    distance = 0

    if result:

        delivery_fee = result[0]

        vehicle = result[1]

        distance = result[2]

    # UPDATE STATUS

    cur.execute("""

    UPDATE donations

    SET status='Accepted'

    WHERE id=?

    """, (id,))

    conn.commit()

    # SAVE TRANSACTION

    cur.execute("""

    INSERT INTO savings(

        amount,

        details,

        vehicle,

        distance

    )

    VALUES(?,?,?,?)

    """, (

        delivery_fee,

        "Food Delivery Completed",

        vehicle,

        distance

    ))

    conn.commit()

    conn.close()

    return redirect('/volunteer')

# ================= ORDER PICKED =================

@app.route('/picked/<int:id>')

def picked(id):

    conn = sqlite3.connect('database.db')

    cur = conn.cursor()

    cur.execute("""

    UPDATE donations

    SET status='Order Picked'

    WHERE id=?

    """, (id,))

    conn.commit()

    conn.close()

    return redirect('/volunteer')


# ================= ON THE WAY =================

@app.route('/ontheway/<int:id>')

def ontheway(id):

    conn = sqlite3.connect('database.db')

    cur = conn.cursor()

    cur.execute("""

    UPDATE donations

    SET status='On The Way'

    WHERE id=?

    """, (id,))

    conn.commit()

    conn.close()

    return redirect('/volunteer')


# ================= DELIVERED =================

@app.route('/delivered/<int:id>')

def delivered(id):

    conn = sqlite3.connect('database.db')

    cur = conn.cursor()

    cur.execute("""

    UPDATE donations

    SET status='Delivered'

    WHERE id=?

    """, (id,))

    conn.commit()

    conn.close()

    return redirect('/volunteer')
# ================= VOLUNTEER =================

@app.route('/volunteer')

def volunteer():

    conn = sqlite3.connect('database.db')

    cur = conn.cursor()

    cur.execute("""

    SELECT * FROM donations

    WHERE status IS NULL

    OR status != 'Accepted'

    """)

    data = cur.fetchall()

    conn.close()

    return render_template(

        'volunteer.html',

        data=data

    )


# ================= SAVINGS =================

@app.route('/savings')

def savings():

    conn = sqlite3.connect('database.db')

    cur = conn.cursor()

    cur.execute("SELECT * FROM savings")

    data = cur.fetchall()

    total = 0

    for item in data:

        total += item[1]

    cur.execute("SELECT * FROM deliveries")

    deliveries = cur.fetchall()

    conn.close()

    return render_template(

        'savings.html',

        data=data,

        total=total,

        deliveries=deliveries

    )


# ================= ADMIN =================

@app.route('/admin', methods=['GET', 'POST'])

def admin():

    if request.method == 'POST':

        password = request.form['password']

        if password == "1234":

            return redirect('/dashboard')

        else:

            return '''

            <h1 style="color:red;text-align:center;">

            Wrong Password ❌

            </h1>

            '''

    return render_template('admin_login.html')


# ================= DASHBOARD =================

@app.route('/dashboard')

def dashboard():

    conn = sqlite3.connect('database.db')

    cur = conn.cursor()

    cur.execute("SELECT * FROM donations")

    data = cur.fetchall()

    total = len(data)

    cur.execute("SELECT * FROM deliveries")

    deliveries = cur.fetchall()

    delivery_total = len(deliveries)

    chart_labels = []

    chart_values = []

    for item in data:

        chart_labels.append(item[1])

        try:

            chart_values.append(int(item[2]))

        except ValueError:

            chart_values.append(1)

    conn.close()

    return render_template(

        'dashboard.html',

        data=data,

        total=total,

        delivery_total=delivery_total,

        chart_labels=json.dumps(chart_labels),

        chart_values=json.dumps(chart_values)

    )


# ================= RUN APP =================

if __name__ == '__main__':

    webbrowser.open("http://127.0.0.1:5000")

    app.run(debug=True, use_reloader=False)