from flask import Flask, render_template, request, redirect, url_for, session
from redis import Redis
from pymongo import MongoClient
from neo4j import GraphDatabase
import os

app = Flask(__name__, template_folder='templates')
app.secret_key = os.urandom(24)

# Connection to redis server 
redis = Redis(host="redis", port=6379)

# Connection to mongodb and create database and collection
mongo = MongoClient("mongodb://nsql-mongodb-1/", username="admin", password="admin")
mymongodb = mongo["mymongodb"]
users = mymongodb["users"]
todo_lists = mymongodb["todo_lists"] 

# not working 
# driver = GraphDatabase.driver("bolt://nsql-neo4j-1:7687")

# {{}} promenna
# {% %} python 
# redirect pro post

@app.route("/homepage")
def homepage():
    if "username" not in session:
        return redirect(url_for("login"))
    
    todo_list = todo_lists.find({"username": session["username"]})

    return render_template("homepage.html", username=session["username"], todo_list=todo_list)

@app.route("/registration", methods=["POST", "GET"])
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
    
    if "username" in session:
        return redirect(url_for("homepage"))
 
    return render_template("registration.html")

@app.route("/")
@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = users.find_one({"username": username}) 

        if user and password == user["password"]:
            session["username"] = username
            return redirect(url_for("homepage"))

    # todo: wrong login
    if "username" in session:
        return redirect(url_for("homepage"))

    return render_template("/login.html")

@app.route("/logout", methods=["POST", "GET"])
def logout():
    if "username" in session:
        session.pop("username", None)

    return redirect(url_for("login"))

@app.route("/create_task", methods=["POST"])
def create_task():
    if "username" in session and request.method == "POST":
        heading = request.form.get("heading")
        deadline = request.form.get("deadline")
        priority = request.form.get("priority")
        description = request.form.get("description")

        # todo id task
        todo_lists.insert_one({
            "username": session["username"],
            "heading": heading, 
            "deadline": deadline,
            "priority": priority,
            "description": description,
            "is_done": False  
        })

    return redirect(url_for('homepage'))

@app.route("/tasks")
def tasks():
    todo_list = todo_lists.find({"username": session["username"]})
    return render_template("/tasks.html", todo_list=todo_list)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)