import re
import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__) 

app.secret_key = 'abcdefgh'
  
app.config['MYSQL_HOST'] = 'db'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'cs353hw4db'
  
mysql = MySQL(app)  

@app.route("/")
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("loggedin"):
        return redirect(url_for("main"))

    message = ""
    if (
        request.method == "POST"
        and "username" in request.form
        and "password" in request.form
    ):
        username = request.form["username"]
        password = request.form["password"]

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = "SELECT * FROM student WHERE sname = %s AND sid = %s"
        values = (username, password)
        cursor.execute(query, values)
        user = cursor.fetchone()

        if user:
            session["loggedin"] = True
            session["sid"] = user["sid"]
            session["sname"] = user["sname"]
            session["bdate"] = user["bdate"]
            session["dept"] = user["dept"]
            session["year"] = user["year"]
            session["gpa"] = user["gpa"]

            return redirect(url_for("main"))
        else:
            message = "Wrong credentials!"

    return render_template("login.html", message=message)


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("loggedin"):
        return redirect(url_for("main"))
    
    message = ""
    if (
        request.method == "POST"
        and request.form.get("username")
        and request.form.get("password")
        and request.form.get("bdate")
        and request.form.get("dept")
        and request.form.get("year")
        and request.form.get("gpa")
    ):
        username = request.form["username"]
        password = request.form["password"]
        bdate = request.form["bdate"]
        dept = request.form["dept"]
        year = request.form["year"]
        gpa = request.form["gpa"]

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = "SELECT * FROM student WHERE sname = %s"
        values = (username,)
        cursor.execute(query, values)
        username_check = cursor.fetchone()

        if username_check:
            message = "Select different username!"
        else:
            query = "INSERT INTO student (sid, sname, bdate, dept, year, gpa) VALUES (%s, %s, %s, %s, %s, %s)"
            values = (password, username, bdate, dept, year, gpa)
            cursor.execute(query, values)
            mysql.connection.commit()
            message = "User successfully created!"

    elif request.method == "POST":
        message = "Please fill all the fields!"

    return render_template("register.html", message=message)


@app.route("/main", methods=["GET", "POST"])
def main():
    message = ""
    if session.get("loggedin"):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = "SELECT DISTINCT c.* FROM company c JOIN apply a ON c.cid = a.cid WHERE a.sid = %s"
        values = (session["sid"],)
        cursor.execute(query, values)
        companies = cursor.fetchall()
    else:
        return redirect(url_for("login"))

    return render_template("main.html", companies=companies)


@app.route("/apply", methods=["GET", "POST"])
def apply():
    sid = session.get("sid")
    gpa = session.get("gpa")
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query = "SELECT COUNT(sid) AS internship_count FROM apply WHERE sid = %s"
    values = (sid,)
    cursor.execute(query, values)
    internship_count = cursor.fetchone().get("internship_count")

    if session.get("loggedin"):
        query = (
            "SELECT DISTINCT c.* FROM company c"
            " WHERE c.cid NOT IN (SELECT cid FROM apply WHERE sid = %s)"
            " AND c.quota > 0"
            " AND c.gpa_threshold <= %s"
        )
        values = (sid, gpa)
        cursor.execute(query, values)
        companies = cursor.fetchall()
        session["available_companies"] = companies

    else:
        return redirect(url_for("login"))


    if not internship_count < 3:
        flash("You already have maximum amount of internships applications!")

    return render_template(
        "apply.html",
        companies=companies,
        can_apply="" if internship_count < 3 else "disabled",
    )


@app.route("/summary", methods=["GET", "POST"])
def summary():
    sid = session.get("sid")
    if session.get("loggedin"):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = "SELECT cname, quota, gpa_threshold FROM ((company NATURAL JOIN apply) NATURAL JOIN student) WHERE sid = %s ORDER BY quota DESC"
        values = (sid,)
        cursor.execute(query, values)
        result1 = cursor.fetchall()

        query = (
            "SELECT MAX(gpa_threshold) AS max_gpa_threshold, MIN(gpa_threshold) AS min_gpa_threshold"
            " FROM ((company NATURAL JOIN apply) NATURAL JOIN student) WHERE sid = %s"
        )
        values = (sid,)
        cursor.execute(query, values)
        result2 = cursor.fetchone()

        maxVal = result2["max_gpa_threshold"]
        minVal = result2["min_gpa_threshold"]

        if maxVal and minVal:
            result2["max_gpa_threshold"] = round(maxVal, 2)
            result2["min_gpa_threshold"] = round(minVal, 2)
        else:
            result2 = None

        query = (
            "SELECT city, COUNT(DISTINCT cid) AS application_count FROM ((company NATURAL JOIN apply) NATURAL JOIN student) WHERE sid = %s"
            " GROUP BY city"
        )
        values = (sid,)
        cursor.execute(query, values)
        result3 = cursor.fetchall()

        query = (
            "SELECT c_max.cname AS company_with_max_quota, c_min.cname AS company_with_min_quota "
            "FROM "
            " (SELECT MAX(quota) AS max, MIN(quota) AS min FROM company WHERE cid IN (SELECT cid FROM apply WHERE sid = %s)) AS subquery"
            " JOIN (SELECT * FROM company WHERE cid IN (SELECT cid FROM apply WHERE sid = %s)) AS c_max ON subquery.max = c_max.quota"
            " JOIN (SELECT * FROM company WHERE cid IN (SELECT cid FROM apply WHERE sid = %s)) AS c_min ON subquery.min = c_min.quota"
        )

        values = (sid, sid, sid)
        cursor.execute(query, values)
        result4 = cursor.fetchall()
    else:
        return redirect(url_for("login"))

    return render_template(
        "summary.html",
        result1=result1,
        result2=result2,
        result3=result3,
        result4=result4,
    )


@app.route("/cancel_internship", methods=["GET"])
def cancel_internship():
    cid = request.args.get("cid")
    sid = session.get("sid")

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    query = "SELECT quota FROM company WHERE cid = %s"
    cursor.execute(query, (cid,))
    current_quota = cursor.fetchone()

    if current_quota:
        current_quota = current_quota["quota"]

    try:
        query = "DELETE FROM apply WHERE sid = %s AND cid = %s"
        values = (sid, cid)
        cursor.execute(query, values)

        query = "UPDATE company SET quota = %s WHERE cid = %s"
        cursor.execute(query, (current_quota + 1, cid))
        mysql.connection.commit()

        flash("Internship canceled successfully.")
    except:
        flash("Internship can not be canceled.")

    return redirect(url_for("main"))


@app.route("/apply_internship", methods=["GET"])
def apply_internship():
    sid = session.get("sid")
    cid = request.args.get("cid")

    availabe_companies = session.pop("available_companies", None)
    exists = False
    if availabe_companies:
        for x in availabe_companies:
            if x.get("cid") == cid:
                exists = True

    if exists:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        query = "SELECT quota FROM company WHERE cid = %s"
        cursor.execute(query, (cid,))
        current_quota = cursor.fetchone()

        if current_quota:
            current_quota = current_quota["quota"]

        try:
            query = "INSERT INTO apply (sid, cid) VALUES (%s, %s)"
            values = (sid, cid)
            cursor.execute(query, values)

            query = "UPDATE company SET quota = %s WHERE cid = %s"
            cursor.execute(query, (current_quota - 1, cid))
            mysql.connection.commit()

            flash("Internship applied successfully.")
        except:
            flash("Internship can not be applied due to an error.")
    else:
        flash("Company is not available.")

    return redirect(url_for("apply"))


@app.route("/logout", methods=["GET"])
def logout():
    session["loggedin"] = False
    session.pop("sid", None)
    session.pop("sname", None)
    session.pop("bdate", None)
    session.pop("dept", None)
    session.pop("year", None)
    session.pop("gpa", None)
    session.pop("available_companies", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
