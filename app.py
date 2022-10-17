import os


from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
uri = os.getenv("DATABASE_URL")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://")
db = SQL(uri)




@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/buy", methods=['GET', 'POST'])
@login_required
def buy():
    if request.method == "POST":
        product = request.form.get("product")
        
        if not product:
            return render_template("apology.html")
        person = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        cash = person[0]["cash"] 
        rows = db.execute("SELECT * FROM products WHERE name = ?", product)
        price = rows[0]["price"]
        final_cash = cash - price
        if final_cash < 0:
            return render_template("apology.html")
        db.execute("UPDATE users SET cash = ? WHERE id = ?", final_cash, session["user_id"])
        now = datetime.now()
        dt = now.strftime("%d/%m/%Y %H:%M:%S")
        db.execute("INSERT INTO purchase (buyer_id, name, price, time) VALUES (?, ?, ?, ?)", session["user_id"], product, price, dt)
        return redirect("/ballance")
    else:
        return render_template("buy.html")

    





@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("apology.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("apology.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("apology.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")








@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()
    if request.method == "POST":
        
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        if not username :
            return render_template("apology.html")
        elif len(rows) != 0:
            return render_template("apology.html")
        elif not password:
            return render_template("apology.html")
        elif not confirmation or confirmation != password:
            return render_template("apology.html")
        else:
            db.execute('INSERT INTO users (username, hash) VALUES (?, ?)', username, generate_password_hash(password))
            rows = db.execute("SELECT * FROM users WHERE username = ?", username)
            session["user_id"] = rows[0]["id"]
            return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        product = request.form.get("product")
        if not product :
            return render_template("apology.html")
        rows = db.execute("SELECT * FROM products WHERE name = ?", product)
        price = rows[0]["price"]
        person = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        cash = person[0]["cash"]
        final_cash = cash + price
        db.execute("UPDATE users SET cash = ? WHERE id = ?", final_cash, session["user_id"])
        db.execute("DELETE FROM purchase WHERE name = ? and buyer_id = ? LIMIT 1", product, session["user_id"])
        return redirect("/ballance")
        

    else:
        rows = db.execute("SELECT * FROM purchase WHERE buyer_id = ? ORDER BY time DESC", session["user_id"])
        if len(rows) != 0:   
            return render_template("sell.html", rows = rows)
        else :
            return render_template("sell.html")


@app.route("/ballance", methods=["GET", "POST"])
@login_required
def ballance():
    """Show history of transactions"""
    rows = db.execute("SELECT * FROM purchase WHERE buyer_id = ? ORDER BY time DESC", session["user_id"])
    person = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    cash = person[0]["cash"]
    if len(rows) != 0:
        return render_template("ballance.html", rows=rows, cash=cash)
    else :
        return render_template("ballance.html", cash=cash)






@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")
        

