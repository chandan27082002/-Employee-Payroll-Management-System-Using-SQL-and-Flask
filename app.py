from flask import Flask, jsonify, request
import psycopg2

app = Flask(__name__)

# Database connection config
DB_NAME = "payroll_db"
DB_USER = "payroll_user"
DB_PASSWORD = "strongpassword"
DB_HOST = "localhost"
DB_PORT = "5432"

# Establish a DB connection
def get_db_connection():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

# Root route
@app.route('/')
def home():
    return "✅ Employee Payroll System API is running!"

# Generate Payroll
@app.route('/generate_payroll', methods=['POST'])
def generate_payroll():
    try:
        data = request.get_json()
        input_month = data.get('month')       # e.g., "May 2025"
        run_date = data.get('run_date')       # e.g., "2025-06-01"

        conn = get_db_connection()
        cur = conn.cursor()

        # Call PostgreSQL function with explicit type casting
        cur.execute("SELECT generate_monthly_payroll_with_attendance(%s::TEXT, %s::DATE);", (input_month, run_date))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": f"Payroll generated for {input_month}!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# View Payroll Data
@app.route('/payrolls', methods=['GET'])
def get_payrolls():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Payroll ORDER BY DateGenerated DESC;")
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()

        payrolls = [dict(zip(columns, row)) for row in rows]
        return jsonify(payrolls)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
@app.route('/test_form', methods=['GET', 'POST'])
def test_form():
    if request.method == 'POST':
        input_month = request.form.get('month')
        run_date = request.form.get('run_date')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT generate_monthly_payroll_with_attendance(%s::TEXT, %s::DATE);", (input_month, run_date))
        conn.commit()
        cur.close()
        conn.close()

        return f"✅ Payroll generated for {input_month}!"

    return '''
        <form method="POST">
            Month: <input type="text" name="month" value="May 2025"><br>
            Run Date: <input type="text" name="run_date" value="2025-06-01"><br>
            <input type="submit" value="Generate Payroll">
        </form>
    '''
