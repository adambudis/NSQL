from flask import Flask, render_template, request, redirect, url_for, session
from redis import Redis
from pymongo import MongoClient
from bson.objectid import ObjectId
from neo4j import GraphDatabase
import os
from datetime import datetime

app = Flask(__name__, template_folder='templates')
app.secret_key = os.urandom(24)

# Connection to redis server 
redis = Redis(host="redis", port=6379)

# Connection to mongodb and create database and collection
mongo = MongoClient("mongodb://nsql-mongodb-1/", username="admin", password="admin")
mymongodb = mongo["mymongodb"]
users_collection = mymongodb["users"]
todo_lists_collection = mymongodb["todo_lists"]
projects_collection = mymongodb["projects"]

# not working 
# driver = GraphDatabase.driver("bolt://nsql-neo4j-1:7687")

# {{}} promenna
# {% %} python 
# redirect pro post

@app.route("/homepage")
def homepage():
    if "username" not in session:
        return redirect(url_for("login"))
    
    todo_list = todo_lists_collection.find({"username": session["username"]})

    return render_template("homepage.html", username=session["username"], todo_list=todo_list)

@app.route("/registration", methods=["POST", "GET"])
def registration():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if users_collection.find_one({'username': username}) or users_collection.find_one({'email': email}):
            # user already exists
            return render_template("registration.html")

        # todo: přidat hash hesla
        users_collection.insert_one({'username': username, 'email': email, 'password': password})
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
        
        user = users_collection.find_one({"username": username}) 

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

@app.route("/projects", methods=["POST", "GET"])
def projects():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")

        projects_collection.insert_one({
            "title": title,
            "time_created": datetime.now().strftime("%Y-%m-%d"),
            "description": description,
            "owner": session["username"],
            "users": ""
        })

    find_projects = projects_collection.find({ 
        "$or": [
            {"owner": session["username"]}, 
            {"users": session["username"]}
        ]
    }) 
    return render_template("/projects.html", username=session["username"], my_projects=find_projects)

@app.route("/delete_project/<_id>")
def delete_project(_id):

    find_project = projects_collection.delete_one({"_id": ObjectId(_id)})
    return redirect(url_for("projects"))

@app.route("/create_task", methods=["POST"])
def create_task():
    if "username" in session and request.method == "POST":
        heading = request.form.get("heading")
        deadline = request.form.get("deadline")
        priority = request.form.get("priority")
        description = request.form.get("description")

        # todo id task
        todo_lists_collection.insert_one({
            "username": session["username"],
            "heading": heading, 
            "deadline": deadline,
            "time_created": datetime.now().strftime("%Y-%m-%d"),
            "priority": priority,
            "description": description,
            "is_done": False  
        })

    return redirect(url_for('homepage'))

@app.route("/task_details/<_id>", methods=["POST", "GET"])
def task_details(_id):
    task = todo_lists_collection.find_one({'_id': ObjectId(_id)})

    return render_template("/task_details.html", username=session["username"], task=task)

@app.route("/tasks")
def tasks():
    todo_list = todo_lists_collection.find({"username": session["username"]})
    return render_template("/tasks.html", username=session["username"], todo_list=todo_list)

@app.route("/profile")
def profile():
    return render_template("/profile.html", username=session["username"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)