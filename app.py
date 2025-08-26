from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import psycopg2
from config import DB_CONFIG, SECRET_KEY  # ✅ Configs
from datetime import date


app = Flask(__name__)
app.secret_key = SECRET_KEY  # ✅ Secret key for session management

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/employees')
def employees():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT EmployeeID, Name, DepartmentID, Position, HireDate FROM payroll.employee;")
    employees = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('employees.html', employees=employees)

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        department_id = request.form['department_id']
        position = request.form['position']
        hire_date = request.form['hire_date']

        cur.execute(
            "INSERT INTO payroll.employee (Name, DepartmentID, Position, HireDate) VALUES (%s, %s, %s, %s)",
            (name, department_id, position, hire_date)
        )
        conn.commit()
        cur.close()
        conn.close()
        flash('Employee added successfully!')
        return redirect(url_for('employees'))

    cur.execute("SELECT DepartmentID, DepartmentName FROM payroll.department")
    departments = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('add_employee.html', departments=departments)

@app.route('/update_employee/<int:id>', methods=['GET', 'POST'])
def update_employee(id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        department_id = request.form['department_id']
        position = request.form['position']
        hire_date = request.form['hire_date']

        cur.execute(
            "UPDATE payroll.employee SET Name=%s, DepartmentID=%s, Position=%s, HireDate=%s WHERE EmployeeID=%s",
            (name, department_id, position, hire_date, id)
        )
        conn.commit()
        flash('Employee updated successfully!')
        return redirect(url_for('employees'))

    cur.execute("SELECT * FROM payroll.employee WHERE EmployeeID = %s", (id,))
    employee = cur.fetchone()

    cur.execute("SELECT DepartmentID, DepartmentName FROM payroll.department")
    departments = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('update_employee.html', employee=employee, departments=departments)

@app.route('/delete_employee/<int:id>')
def delete_employee(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM payroll.employee WHERE EmployeeID = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    flash('Employee deleted successfully!')
    return redirect(url_for('employees'))

@app.route('/departments')
def departments():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DepartmentID, DepartmentName FROM payroll.department")
    departments = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('departments.html', departments=departments)

@app.route('/add_department', methods=['GET', 'POST'])
def add_department():
    if request.method == 'POST':
        department_id = request.form['department_id']
        department_name = request.form['department_name']

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # Debug: Print connected database user
            cur.execute("SELECT current_user;")
            user = cur.fetchone()[0]
            print(f"Connected as: {user}")  # Will print in your terminal

            # Use schema-qualified table name (if table is in 'payroll' schema)
            cur.execute("""
                INSERT INTO payroll.Department (DepartmentID, DepartmentName)
                VALUES (%s, %s)
            """, (department_id, department_name))

            conn.commit()
            flash("Department added successfully!", "success")
        except psycopg2.IntegrityError:
            conn.rollback()
            flash("Department ID already exists. Please use a unique ID.", "danger")
        except psycopg2.errors.InsufficientPrivilege:
            conn.rollback()
            flash("Permission denied. Check database privileges for your user.", "danger")
        except Exception as e:
            conn.rollback()
            flash(f"An unexpected error occurred: {str(e)}", "danger")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('add_department'))

    return render_template('add_department.html')


@app.route('/update_department/<int:id>', methods=['GET', 'POST'])
def update_department(id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        name = request.form['department_name']
        cur.execute("UPDATE payroll.department SET DepartmentName = %s WHERE DepartmentID = %s", (name, id))
        conn.commit()
        flash('Department updated successfully!')
        return redirect(url_for('departments'))

    cur.execute("SELECT * FROM payroll.department WHERE DepartmentID = %s", (id,))
    department = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('update_department.html', department=department)

@app.route('/delete_department/<int:id>')
def delete_department(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM payroll.department WHERE DepartmentID = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    flash('Department deleted successfully!')
    return redirect(url_for('departments'))

from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date, datetime
import psycopg2
from datetime import date, datetime


@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SET search_path TO payroll;")

    if request.method == 'POST':
        date_value = request.form['date']
        try:
            date_obj = datetime.strptime(date_value, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format!", "danger")
            return redirect(url_for('attendance'))

        for emp_id in request.form.getlist('employee'):
            status = request.form.get(f'status_{emp_id}')
            overtime = request.form.get(f'overtime_{emp_id}', 0)

            try:
                cur.execute("""
                    INSERT INTO attendance (EmployeeID, Date, Status, OvertimeHrs)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (EmployeeID, Date) DO UPDATE 
                    SET Status = EXCLUDED.Status,
                        OvertimeHrs = EXCLUDED.OvertimeHrs;
                """, (emp_id, date_obj, status, overtime))
            except Exception as e:
                conn.rollback()
                flash(f"Error saving attendance for Employee ID {emp_id}: {str(e)}", "danger")
                continue

        conn.commit()
        flash("Attendance submitted successfully!", "success")
        return redirect(url_for('attendance'))

    # For GET: fetch employees
    cur.execute("SELECT EmployeeID, Name FROM employee")
    employees = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('attendance.html', employees=employees, today=date.today().strftime('%Y-%m-%d'))

from datetime import datetime, date
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, date
import psycopg2

@app.route('/view_attendance', methods=['GET', 'POST'])
def view_attendance():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SET search_path TO payroll;")

    if request.method == 'POST':
        selected_date_str = request.form['date']
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format! Please select a date using the date picker.", "danger")
            return redirect(url_for('view_attendance'))
    else:
        selected_date = date.today()

    print("⏳ Fetching attendance for:", selected_date)

    cur.execute("""
        SELECT a.AttendanceID, e.Name, a.EmployeeID, a.Date, a.Status, a.OvertimeHrs
        FROM attendance a
        JOIN employee e ON a.EmployeeID = e.EmployeeID
        WHERE a.Date = %s
        ORDER BY a.EmployeeID
    """, (selected_date,))
    
    records = cur.fetchall()
    cur.close()
    conn.close()

    if not records:
        flash("No attendance records found for the selected date.", "warning")

    return render_template('view_attendance.html', attendance_records=records, today=selected_date.strftime('%Y-%m-%d'))

@app.route('/update_attendance', methods=['POST'])
def update_attendance():
    attendance_id = request.form['attendance_id']
    new_date = request.form['date']
    new_status = request.form['status']
    new_overtime = request.form['overtime']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SET search_path TO payroll;")

    try:
        cur.execute("""
            UPDATE attendance
            SET Date = %s, Status = %s, OvertimeHrs = %s
            WHERE AttendanceID = %s
        """, (new_date, new_status, new_overtime, attendance_id))

        conn.commit()
        flash("Attendance record updated successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error updating attendance: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('view_attendance'))

@app.route('/salary_structure', methods=['GET', 'POST'])
def salary_structure():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SET search_path TO payroll;")  # Set schema once

    if request.method == 'POST':
        emp_id = request.form['employee_id']
        base_pay = request.form['base_pay']
        hra = request.form.get('hra', 0)
        bonus = request.form.get('bonus', 0)

        cur.execute("""
            INSERT INTO SalaryStructure (EmployeeID, BasicPay, HRA, Bonus)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (EmployeeID) DO UPDATE
            SET BasicPay = EXCLUDED.BasicPay,
                HRA = EXCLUDED.HRA,
                Bonus = EXCLUDED.Bonus;
        """, (emp_id, base_pay, hra, bonus))
        conn.commit()
        flash('Salary structure saved/updated.')
        return redirect(url_for('salary_structure'))

    # Fetch all employees for dropdown
    cur.execute("SELECT EmployeeID, Name FROM employee ORDER BY EmployeeID")
    employees = cur.fetchall()

    # Fetch salary data joined with employee names
    cur.execute("""
        SELECT e.EmployeeID, e.Name, s.BasicPay, s.HRA, s.Bonus
        FROM employee e
        LEFT JOIN SalaryStructure s ON e.EmployeeID = s.EmployeeID
        ORDER BY e.EmployeeID
    """)
    salaries = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('salary_structure.html', employees=employees, salaries=salaries)

@app.route('/deductions', methods=['GET', 'POST'])
def deductions():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        emp_id = request.form['employee_id']
        tax_percent = request.form['tax_percent']
        pf_percent = request.form['pf_percent']

        cur.execute("""
            INSERT INTO payroll.deductions (EmployeeID, TaxPercent, PFPercent)
            VALUES (%s, %s, %s)
            ON CONFLICT (EmployeeID) DO UPDATE
            SET TaxPercent = EXCLUDED.TaxPercent,
                PFPercent = EXCLUDED.PFPercent;
        """, (emp_id, tax_percent, pf_percent))
        conn.commit()
        flash('Deductions saved/updated successfully!')
        return redirect(url_for('deductions'))

    cur.execute("""
        SELECT e.EmployeeID, e.Name, d.TaxPercent, d.PFPercent
        FROM payroll.employee e
        LEFT JOIN payroll.deductions d ON e.EmployeeID = d.EmployeeID
    """)
    deductions_data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('deductions.html', deductions=deductions_data)

from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
import psycopg2

@app.route('/generate_payroll', methods=['GET', 'POST'])
def generate_payroll():
    if request.method == 'POST':
        month_input = request.form['month']  # e.g., "May 2025"

        try:
            # Validate and format
            dt = datetime.strptime(month_input, "%B %Y")
            formatted_month = dt.strftime("%B %Y")  # e.g., "May 2025"
            run_date = datetime.today().date()
        except ValueError:
            flash("Invalid month format. Use 'Month YYYY' like 'May 2025'.")
            return redirect(url_for('generate_payroll'))

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT payroll.generate_monthly_payroll_with_attendance(%s, %s);", (formatted_month, run_date))
            conn.commit()
            cur.close()
            conn.close()
            flash(f"Payroll successfully generated for {formatted_month}")
        except Exception as e:
            flash(f"Error generating payroll: {str(e)}")

        return redirect(url_for('payroll'))

    return render_template('generate_payroll.html')

@app.route('/payroll')
def payroll():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.EmployeeID, e.Name, p.Month, p.GrossPay, p.TotalDeductions, p.NetPay, p.DateGenerated
        FROM payroll.Payroll p
        JOIN payroll.Employee e ON p.EmployeeID = e.EmployeeID
        ORDER BY p.DateGenerated DESC;
    """)
    payroll_data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('payroll.html', payrolls=payroll_data)

@app.route('/delete_payroll', methods=['POST'])
def delete_payroll():
    employee_id = request.form['employee_id']
    month = request.form['month']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM payroll.payroll WHERE employeeid = %s AND month = %s", (employee_id, month))
    conn.commit()
    cur.close()
    conn.close()

    flash('Payroll record deleted successfully.')
    return redirect(url_for('payroll'))
# Import DB_CONFIG and SECRET_KEY directly from config.py
from config import DB_CONFIG, SECRET_KEY
from flask import Flask, render_template, request
import psycopg2


app.config['SECRET_KEY'] = SECRET_KEY  # Set the secret key for Flask
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed", 500
    cur = conn.cursor()

    # Donut Chart: Employee count by department
    cur.execute("""
        SELECT d.DepartmentName, COUNT(e.EmployeeID)
        FROM payroll.Department d
        LEFT JOIN payroll.Employee e ON d.DepartmentID = e.DepartmentID
        GROUP BY d.DepartmentName;
    """)
    dept_data = cur.fetchall()

    # Net Pay Filter by Month
    month_filter = 'All'
    netpay = 0
    if request.method == 'POST':
        month_filter = request.form['month']
        cur.execute("SELECT SUM(NetPay) FROM payroll.Payroll WHERE Month = %s", (month_filter,))
        result = cur.fetchone()
        netpay = result[0] if result and result[0] is not None else 0

    cur.close()
    conn.close()

    return render_template('dashboard.html',
                           dept_data=dept_data,
                           netpay=netpay,
                           month_filter=month_filter)

if __name__ == '__main__':
    app.run(debug=True)