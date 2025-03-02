from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from redis import Redis
from pymongo import MongoClient
from bson.objectid import ObjectId
from neo4j import GraphDatabase
import os
from datetime import datetime
import bcrypt
from dotenv import load_dotenv

app = Flask(__name__, template_folder='templates')
app.secret_key = os.urandom(24)

# Načtení proměnných prostředí
load_dotenv()

# Získání hodnot z prostředí
MONGO_HOST = os.getenv("MONGO_HOST", "nsql-mongodb-1")
MONGO_USER = os.getenv("MONGO_USER", "admin")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "password")

# Připojení k MongoDB s použitím proměnných prostředí
mongo = MongoClient("mongodb://nsql-mongodb-1/", username=MONGO_USER, password=MONGO_PASSWORD)
mymongodb = mongo["mymongodb"]
users_collection = mymongodb["users"]
tasks_collection = mymongodb["tasks"]
projects_collection = mymongodb["projects"]
invitations_collection = mymongodb["invitations"]

# neo4j server
# driver = GraphDatabase.driver("bolt://nsql-neo4j-1:7687", auth=("neo4j", "adminheslo"))
# neo4j_session = driver.session()

# {{}} promenna
# {% %} python 
# redirect pro post


def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return decorated_function

####################################################################################

#####   LOGIN / REGISTRATION / LOGOUT   

####################################################################################

@app.route("/registration", methods=["POST", "GET"])
def registration():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if users_collection.find_one({'username': username}) or users_collection.find_one({'email': email}):
            # user already exists
            return render_template("registration.html")

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        users_collection.insert_one({'username': username, 'email': email, 'password': hashed_password})

        return redirect(url_for("login"))
    
    if "username" in session:
        return redirect(url_for("homepage"))
 
    return render_template("registration.html")
 
@app.route("/")
@app.route("/login", methods=["POST", "GET"])
def login():
    if "username" in session:
        return redirect(url_for("homepage"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = users_collection.find_one({"username": username}) 

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session["username"] = username
            return redirect(url_for("homepage"))

    return render_template("/login.html")

@app.route("/logout", methods=["POST", "GET"])
def logout():
    if "username" in session:
        session.pop("username", None)

    return redirect(url_for("login"))


####################################################################################

######   PROJECTS   

####################################################################################

@app.route("/projects", methods=["POST", "GET"])
@login_required
def projects():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")

        projects_collection.insert_one({
            "title": title,
            "time_created": datetime.now().strftime("%Y-%m-%d"),
            "description": description,
            "owner": session["username"],
            "users": []
        })

    find_projects = projects_collection.find({ 
        "$or": [
            {"owner": session["username"]}, 
            {"users": session["username"]}
        ]
    }) 

    return render_template("/projects.html", username=session["username"], projects=find_projects)

@app.route("/delete_project/<_id>")
@login_required
def delete_project(_id):
    
    if session["username"] == projects_collection.find_one({"_id": ObjectId(_id)})['owner']:
        projects_collection.delete_one({"_id": ObjectId(_id)})

    return redirect(url_for("projects"))

@app.route("/leave_project/<_id>")
@login_required
def leave_project(_id):

    if session["username"] in projects_collection.find_one({"_id": ObjectId(_id)})["users"]:
        projects_collection.update_one({"_id": ObjectId(_id)}, {"$pull": {"users": session["username"]}})

    return redirect(url_for("projects"))

@app.route("/project_details/<_id>", methods=["POST", "GET"])
@login_required
def project_details(_id):

    project = projects_collection.find_one({'_id': ObjectId(_id)})
    if project["owner"] != session["username"]:
        return redirect(url_for("homepage")) 
    
    if request.method == "POST":
        new_title = request.form.get("title")
        new_description = request.form.get("description")

        projects_collection.update_one({"_id": ObjectId(_id)}, {"$set": {"title": new_title, "description": new_description}})
        return redirect(url_for("projects"))

    return render_template("/project_details.html", username=session["username"], project=project)

@app.route("/add_user/<_id>", methods=["POST"])
@login_required
def add_user(_id):

    if request.method == "POST":
        invited_user = users_collection.find_one({"username": request.form.get("add_user")})

        if not invited_user or invited_user["username"] in projects_collection.find_one({"_id": ObjectId(_id)})["users"]:
            return redirect(url_for("project_details", _id=_id))

        if invited_user:
            invitations_collection.insert_one({
                "invited_user": invited_user["username"],
                "sender_user": session["username"],
                "id_project": ObjectId(_id)
            })

            return redirect(url_for("project_details", _id=_id))

    return redirect(url_for("homepage")) 

@app.route("/remove_user/<_id>", methods=["POST"])
@login_required
def remove_user(_id):
    if request.method == "POST":
        user = users_collection.find_one({"username": request.form.get("remove_user")})
        if user:
            projects_collection.update_one({"_id": ObjectId(_id)}, {"$pull": {"users": user["username"]}})
            return redirect(url_for("project_details", _id=_id))
    return redirect(url_for("homepage"))

####################################################################################

######   TASKS

####################################################################################

@app.route("/project_tasks/<_id>", methods=["POST", "GET"])
@login_required
def project_tasks(_id):
    if request.method == "POST":
        heading = request.form.get("heading")
        deadline = request.form.get("deadline")
        priority = request.form.get("priority")
        description = request.form.get("description")

        tasks_collection.insert_one({
            "username": session["username"],
            "id_project": ObjectId(_id),
            "heading": heading, 
            "deadline": deadline,
            "time_created": datetime.now().strftime("%Y-%m-%d"),
            "priority": priority,
            "description": description,
            "is_done": False  
        })

    find_project = projects_collection.find_one({"_id": ObjectId(_id)})
    if session["username"] != find_project["owner"] and session["username"] not in find_project["users"]:
        return redirect(url_for("homepage"))
    
    find_tasks = tasks_collection.find({"id_project": ObjectId(_id)})
     
    return render_template("/project_tasks.html", username=session["username"], tasks=find_tasks, project=find_project)

@app.route("/task_details/<_id>", methods=["POST", "GET"])
@login_required
def task_details(_id):
    task = tasks_collection.find_one({'_id': ObjectId(_id)})
    project = projects_collection.find_one({"_id": ObjectId(task["id_project"])})
    
    if session["username"] != project["owner"] and session["username"] not in project["users"]:
        return redirect(url_for("homepage"))

    if request.method == "POST":
        new_heading = request.form.get("heading")
        new_description = request.form.get("description")
        new_deadline = request.form.get("deadline")
        new_priority = request.form.get("priority")

        tasks_collection.update_one({"_id": ObjectId(_id)}, {"$set": {
            "heading": new_heading, 
            "description": new_description,
            "deadline": new_deadline,
            "priority": new_priority
        }})

        return redirect(url_for("project_tasks", _id=ObjectId(project["_id"])))
        
    return render_template("/task_details.html", username=session["username"], task=task)

# dekorator
@app.route("/delete_task/<_id>")
@login_required
def delete_task(_id):
    task = tasks_collection.find_one({"_id": ObjectId(_id)})
    project = projects_collection.find_one({"_id": task["id_project"]})
    if session["username"] != project["owner"] and session["username"] not in project["users"]:
        return redirect(url_for("homepage"))
    tasks_collection.delete_one(task)
    return redirect(url_for("project_tasks", _id=project["_id"]))

@app.route("/complete_task/<_id>")
@login_required
def complete_task(_id):
    task = tasks_collection.find_one({"_id": ObjectId(_id)})
    project = projects_collection.find_one({"_id": task["id_project"]})
    if session["username"] != project["owner"] and session["username"] not in project["users"]:
        return redirect(url_for("homepage"))
    tasks_collection.update_one(task, {"$set": {"is_done": True}})
    return redirect(url_for("project_tasks", _id=project["_id"]))

@app.route("/uncomplete_task/<_id>")
@login_required
def uncomplete_task(_id):
    task = tasks_collection.find_one({"_id": ObjectId(_id)})
    project = projects_collection.find_one({"_id": task["id_project"]})
    if session["username"] != project["owner"] and session["username"] not in project["users"]:
        return redirect(url_for("homepage"))
    tasks_collection.update_one(task, {"$set": {"is_done": False}})
    return redirect(url_for("project_tasks", _id=project["_id"]))

@app.route("/tasks")
@login_required
def tasks():
    find_tasks = tasks_collection.find({"username": session["username"]})
    return render_template("/tasks.html", username=session["username"], tasks=find_tasks)


####################################################################################

#####   HOMEPAGE

####################################################################################

@app.route("/homepage")
@login_required
def homepage():
    find_projects = projects_collection.find({"owner": session["username"]}).limit(3)

    return render_template("homepage.html", username=session["username"], projects=find_projects)


####################################################################################

#####   PROFILE

####################################################################################

@app.route("/profile")
@login_required
def profile():
    
    get_invitations = invitations_collection.find({"invited_user": session["username"]})
    processed_invitations = []
    for invitation in get_invitations:
        project = projects_collection.find_one({"_id": ObjectId(invitation["id_project"])})
        if project:
            invitation["title"] = project["title"]
            processed_invitations.append(invitation)
    
    return render_template("/profile.html", username=session["username"], invitations=processed_invitations)

@app.route("/accept_invitation/<_id>")
@login_required
def accept_invitation(_id):

    get_invitation = invitations_collection.find_one_and_delete({"_id": ObjectId(_id)})
    projects_collection.update_one({"_id": ObjectId(get_invitation["id_project"])}, {"$push": {"users": session["username"]}})

    return redirect(url_for("profile")) 

@app.route("/decline_invitation/<_id>")
@login_required
def decline_invitation(_id):
    
    invitations_collection.delete_one({"_id": ObjectId(_id)})

    return redirect(url_for("profile")) 

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)