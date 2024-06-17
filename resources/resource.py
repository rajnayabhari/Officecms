from flask import Blueprint, jsonify, request, session
from database import get_db_connection
import hashlib
from psycopg2.extras import RealDictCursor

api_bp = Blueprint('api', __name__)
customer_view_bp = Blueprint('customer_view', __name__)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

@api_bp.route('/signin', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM LOGIN WHERE EMAIL = %s", (email,))
                user = cursor.fetchone()
                if user and verify_password(user[3], password):  # Assuming password is stored in 'password'
                    session['user_id'] = user['id']
                    session['role'] = user['role']
                    session['username'] = user['username']
                    return jsonify({"message": "Login successful"}), 200
                else:
                    return jsonify({"error": "Invalid email or password"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@customer_view_bp.route('/customerview', methods=['GET'])
def customerview():
    role = session.get('role')
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT initcap(customer_name), contact_no, customer_id FROM customers")
                items = cursor.fetchall()
                customers = []
                for item in items:
                    customers.append({
                        "customer_name": item[0],
                        "contact_no": item[1],
                        "customer_id": item[2],
                        "role": role
                    })
                return jsonify(customers), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
