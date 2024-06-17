from flask import Flask
from database import get_db_connection,database
# import matplotlib.pyplot as plt
# import seaborn as sns
# import pandas as pd
import hashlib
import os 
import re
from functools import wraps
from flask import Flask, request, render_template, redirect, session,url_for,abort 
from datetime import datetime
app = Flask(__name__)


#api
from resources.resource import api_bp,customer_view_bp
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(customer_view_bp, url_prefix='/customer_view')




# Get the current date and time
now = datetime.now()
date=now.strftime("%Y-%m-%d")
time=now.strftime("%H:%M")
print(date,time)
app.secret_key = os.urandom(24)
regex_email = re.compile(r'^[a-zA-Z0-9._%+-]+@gmail\.com$')
regex_pass = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')

# Hashing of password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

def generate_certificate_number(prefix="CRF-"):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT MAX(Certificate_no) FROM detail")
                max_certificate_number = cursor.fetchone()[0]
                if max_certificate_number is None:
                    return prefix + "1"
                else:
                    numeric_part = int(max_certificate_number.split("-")[-1])
                    new_certificate_no = numeric_part + 1
                    return f"{prefix}{new_certificate_no}"
    except Exception as e:
        raise e
      

def get_customer_name():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT customer_name FROM customers")
                customer_names = [row[0] for row in cursor.fetchall()]
                print(customer_names)
    except Exception as e:
        return render_template('error.html', info=str(e))
    return customer_names

@app.route('/search', methods=['GET'])
@login_required
def search():
    if 'role' not in session:
        return redirect(url_for('signin'))
    
    try:
        query = request.args.get('query')
        if query is None:
            return render_template("error.html", info="No search  provided.")

        wildcard_query = f"%{query.lower()}%"

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Corrected SQL query with matching parameter count
                cursor.execute("""
                    SELECT * FROM detail
                    WHERE date LIKE %s
                       OR lower(customer_name) LIKE %s
                       OR lower(status) LIKE %s
                       OR lower(username) = %s
                """, (query, wildcard_query, wildcard_query, query.lower()))
                
                data = cursor.fetchall()

                # Corrected count query to match the search criteria
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM Detail
                    WHERE lower(status) = 'pending'
                """)
                
                total = cursor.fetchone()[0]
                role=session['role']
                name=session['username']

                if data:
                        return render_template('homepage.html', items=data, total=total,role=role,name=name.capitalize())


                else:
                     return redirect(url_for('home' , info="No Corresponding Issue "))

    except Exception as e:
        return render_template('error.html', info=str(e),role=session['role'])

@app.route("/")
def root():
    try:
       database()
    except Exception as e:
        return render_template('error.html', info=str(e))
    return render_template("signin.html")

@app.route('/signup', methods=['POST'])
def register():
    try:
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confpass = request.form.get('confirm_password')

        if not (username and email and password and confpass):
            raise ValueError("All fields are required")

        if not re.match(regex_email, email):
            raise ValueError("Invalid email address")

        if not re.match(regex_pass, password):
            raise ValueError("Password must contain at least 1 uppercase, 1 lowercase, 1 digit, 1 special character, and be at least 8 characters long")

        if password != confpass:
            raise ValueError("Password and confirm password don't match")
                
        hashed_password = hash_password(password)
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM LOGIN WHERE EMAIL = %s", (email,))
                if cursor.fetchone():
                    raise ValueError("Email already registered")
                cursor.execute("INSERT INTO LOGIN(USERNAME, EMAIL, PASSWORD,Role) VALUES (%s, %s, %s,%s)", (username, email, hashed_password,'user'))
                conn.commit()
        return render_template('signin.html')
        
    except Exception as e:
        return render_template('signin.html', info=str(e))     
    
@app.route('/signin', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM LOGIN WHERE EMAIL = %s", (email,))
                user = cursor.fetchone()
                if user and verify_password(user[3], password):
                    session['user_id'] = user[0]
                    session['role'] = user[4]
                    session['username']=user[1]
                    return redirect('/home')
    except Exception as e:
        return render_template('signin.html', info=e)

    return render_template('signin.html', info="Invalid email or password")

@app.route('/home')
def home():
    info=request.args.get('info')
    if 'role' in session:
        role = session['role']
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM detail
                    ORDER BY certificate_no DESC
                    """
                )
                items = cursor.fetchall()
                name = session['username']
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM Detail
                    WHERE lower(status) = 'pending'
                """)
                
                total = cursor.fetchone()[0]
                cursor.close()
            # items is a list of tuples, so you cannot call capitalize() on it directly.
            # Instead, iterate through items if needed for further processing.
            # Assuming you want to capitalize strings within the items, do so in your template if needed.
            return render_template('homepage.html', role=role, name=name.capitalize(), items=items,total=total,info=info)
        
        except Exception as e:
            return render_template('signin.html', info=str(e))
    else:
        return redirect('/')
    
    
@app.route("/customer")    
@login_required
def customer():
    role=session['role']
    return render_template("customerregister.html",role=role)
    
@app.route("/registercustomer" , methods=['POST'])
@login_required
def registercustomer():
    try:    
        name=request.form.get('customername')
        contact=request.form.get('customercontact')
        print(name,contact)
        try:
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO customers(
                                customer_name,
                                contact_no
                            )
                            VALUES (%s, %s)""", 
                            (name,contact
                            ))
                        conn.commit()
                        return redirect('/customer')
        except Exception as e:
                conn.rollback()
                return str(e)
                    
    except Exception as e:
        return str(e)
       
    
@app.route('/customerview', methods=['GET']) 
@login_required
def customerview():
    role=session['role']
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT initcap(customer_name), contact_no,customer_id FROM customers")
                items=cursor.fetchall()
                
        return render_template('customerview.html', items=items, role=role)
    except Exception as e:
            return render_template('error.html',info= f"An error occurred: {str(e)}")
    
   
@app.route('/userlist', methods=['GET'])
@login_required
def userlist():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT initcap(username), email,initcap(role) FROM login")
                items=cursor.fetchall()
                role=session['role']
                
        return render_template('Userlist.html', items=items,role=role)
    except Exception as e:
            return render_template('error.html',info= f"An error occurred: {str(e)}")
        
        
@app.route('/register')
@login_required
def register1():
    role=session['role']
    customer_names = get_customer_name()
    print(customer_names)
    return render_template('registerlog.html',role=role, customer_names=customer_names,date=date,time=time)

@app.route('/registerlog', methods=['POST'])
@login_required
def registerlog():
    customer_name=request.form.get('customername')
    status=request.form.get('status')
    issue=request.form.get('issue')
    certificate_no=generate_certificate_number()
    user=session['username']
    try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO Detail(
                            Certificate_no,
                            date,
                            time,
                            customer_name,
                            status,
                            issue,
                            username
                            )
                        VALUES (%s, %s,%s, %s, %s, %s, %s)""", 
                        (certificate_no,date,time, customer_name, status, issue, user))
                    conn.commit()
                    return redirect('/register')
    except Exception as e:
            conn.rollback()
            return str(e)
                    
    
    
        
@app.route('/updateuserrole/<string:item_id>', methods=['GET', 'POST'])
@login_required
def updateuserrole(item_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('signin'))

    if request.method == 'POST':
        new_role = request.form['role']
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE LOGIN SET role = %s WHERE email = %s", (new_role, item_id))
                conn.commit()
        return redirect(url_for('userlist'))
    role=session['role']
    return render_template('updateuserrole.html',role=role, email=item_id)

# Route to delete a user
@app.route('/deleteuser/<string:item_id>', methods=['GET','POST'])
@login_required
def deleteuser(item_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('/'))
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM LOGIN WHERE email = %s", (item_id,))
                conn.commit()
    
    except Exception as e:
        return render_template('error.html',info= f"User cannot be deleted first delete data{str(e)}")
    return redirect(url_for('userlist'))     
  
@app.route('/updatecustomer/<string:item_id>', methods=['GET', 'POST'])
@login_required
def updatecustomer(item_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('/'))

    if request.method == 'POST':
        new_name= request.form.get('customername')
        new_contact=request.form.get('customercontact')
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE customers SET customer_name = %s,contact_no=%s WHERE customer_id=%s", (new_name, new_contact, item_id))
                conn.commit()
            return redirect(url_for('customerview'))
    else:
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        # Fetch item details from database
                        cursor.execute("SELECT * FROM customers WHERE customer_id = %s", (item_id,))
                        item = cursor.fetchone()
                        print(item)
                if item:
                    role=session['role']
                    # Render update template with item details
                    return render_template('updatecustomer.html',role=role, item=item)
                else:
                    # Render error template if item not found
                    return render_template('error.html', info="Entry not found"), 404
            except Exception as e:
                # Render error template with relevant error message
                return render_template('error.html', info=f"Update page loading error: {e}")


# Route to delete a user
@app.route('/deletecustomer/<string:item_id>', methods=['GET','POST'])
@login_required
def deletecustomer(item_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('/'))
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM customers WHERE customer_id = %s", (item_id,))
                conn.commit()
    
    except Exception as e:
        return render_template('error.html',info= f"User cannot be deleted first delete data{str(e)}")
    return redirect(url_for('customerview'))  
 
@app.route('/attendance') 
@login_required
def attendance():
    role=session['role']
    name=session['username']
    info = request.args.get('info')  # Retrieve the info query parameter

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("select * from attendance order by date desc")
                items=cursor.fetchall()
                
    except Exception as e:
        return render_template('error.html',info=e)
    return render_template('attendance.html',date=date,time=time,name=name,items=items,role=role,info=info)


@app.route('/registerattendance',methods=['POST'])
@login_required
def registerattendance():
    name=session['username']
    status=request.form.get('status')
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("select name,date from attendance where name=%s and date=%s",(name,date))
                verify=cursor.fetchone()
                print(verify)
                if verify==None:    
                    cursor.execute("""
                                Insert into attendance(
                                    name,
                                    date,
                                    time,
                                    status
                                )
                                values(%s,%s,%s,%s)
                                """,(name,date,time,status))
                    conn.commit()
                else:
                    return redirect(url_for('attendance' , info="Attendance already registered "))

    except Exception as e:
        return render_template('error.html',info=e)
    
    return redirect(url_for('attendance',info="Attendance registered successfully"))
    

@app.route('/updateissue/<string:item_id>', methods=['GET', 'POST'])
@login_required
def updateissue(item_id):
    # Ensure the user is authenticated and has a valid role in the session
    if 'role' not in session:
        return redirect(url_for('/'))

    if request.method == 'POST':
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Get form data
                    customer_name=request.form.get('customername')
                    status=request.form.get('status')
                    issue=request.form.get('issue')
                    # Construct and execute the SQL update query
                    cursor.execute("""
                        UPDATE Detail
                        SET
                            customer_name =%s,
                            status =%s,
                            issue =%s
                            WHERE certificate_no = %s
                            """, 
                        (customer_name, status, issue,item_id))
                    conn.commit()
            # Redirect based on role

            return redirect(url_for('home'))

        except Exception as e:
            # Render error template with relevant error message
            return render_template('error.html', info=f"Update error: {e}",role=session['role'])
    else:
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    customer_names = get_customer_name()

                    # Fetch item details from database
                    cursor.execute("SELECT * FROM Detail WHERE certificate_no = %s", (item_id,))
                    item = cursor.fetchone()
                    print(item)
            if item:
                role=session['role']
                # Render update template with item details
                return render_template('updatelog.html',role=role, item=item,customer_names=customer_names)
            else:
                # Render error template if item not found
                return render_template('error.html', info="Issue not found"), 404
        except Exception as e:
            # Render error template with relevant error message
            return render_template('error.html', info=f"Update page loading error: {e}",role=session['role'])  
  
    
   
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")

