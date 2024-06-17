import psycopg2
import hashlib


def get_db_connection():
    return psycopg2.connect(
        database="cms",
        user="postgres",
        password="@hybesty123",
        host="127.0.0.1",
        port=5432
    )
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()   


def database():
    email='raj@gmail.com'       
    password='admin'
    username='raj'
    hashed_password = hash_password(password)
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS LOGIN(
            USER_ID SERIAL PRIMARY KEY NOT NULL,
            USERNAME VARCHAR(250) NOT NULL,
            EMAIL VARCHAR(250) NOT NULL UNIQUE,
            PASSWORD VARCHAR(250) NOT NULL,
            ROLE VARCHAR(250) NOT NULL
            );
            INSERT INTO LOGIN (username, password, email, role)
            SELECT %s, %s, %s, %s
            WHERE NOT EXISTS (
                SELECT 1 FROM LOGIN WHERE email = %s
            );
            """, (username, hashed_password, email, 'admin', email)); 
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id SERIAL PRIMARY KEY,
                    customer_name VARCHAR(250) not null,
                    contact_no VARCHAR(15) NOT NULL
                );
                """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Detail (
                Certificate_no VARCHAR(250) PRIMARY KEY,
                date VARCHAR(50) NOT NULL,
                time varchar(50) not null,
                customer_name varchar(250) NOT NULL,
                issue VARCHAR(350) NOT NULL,
                status VARCHAR(60) NOT NULL,
                username VARCHAR(250) NOT NULL
            );
                """)  
            cursor.execute("""
            create table if not exists attendance(
                name varchar(350) not null,
                date varchar(100) not null,
                time varchar(50) not null,
                status varchar(350) not null
            );
                """) 
        conn.commit()