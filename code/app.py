from flask import Flask, render_template, request, redirect, url_for
from redis import Redis
from pymongo import MongoClient
from neo4j import GraphDatabase

app = Flask(__name__, template_folder='templates')

# Connection to redis server 
redis = Redis(host="redis", port=6379)

mongo = MongoClient("mongodb://nsql-mongodb-1/", username="admin", password="admin")
mymongodb = mongo["mymongodb"]
users = mymongodb["users"]

# not working 
# driver = GraphDatabase.driver("bolt://nsql-neo4j-1:7687")

# {{}} promenna
# {% %} python 
# redirect pro post


@app.route("/")
@app.route("/index")
def index():
    #kdykoliv někdo zažádá o endpoint index, tak se zvýší v Redis databázi záznam s klíčem homepage_requests o 1
    redis.incr("homepage_requests")
    counter = str(redis.get("homepage_requests"), "utf-8")
    #redis čítač pošleme do šablony index.html, kde ho následně jako Jinja2 proměnnou vypisujeme na obrazovku
    return render_template("index.html", view_count=counter)

@app.route("/registration", methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if users.find_one({'username': username}) or users.find_one({'email': email}):
            # user already exists
            return render_template("registration.html")

        # todo: přidat hash hesla
        users.insert_one({'username': username, 'email': email, 'password': password})
        return redirect(url_for("login"))
 
    return render_template("registration.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = users.find_one({"username": username}) 

        if user and password == user["password"]:
            return redirect(url_for("index"))

    # todo: wrong login
    return render_template("/login.html")

@app.route("/logout")
def logout():
    pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)