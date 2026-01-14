import psycopg2

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port="5433",
        database="hospital",
        user="hospital_user",
        password="hospital_pass"
    )
