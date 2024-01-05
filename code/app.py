from flask import Flask, render_template, request
from redis import Redis
import pymongo
from neo4j import GraphDatabase

app = Flask(__name__, template_folder='templates')

redis = Redis(host="redis", port=6379)

myclient = pymongo.MongoClient("mongodb://nsql-mongodb-1/", username="admin", password="admin")
mydb = myclient["mydatabase"]

driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "adminpass"))

# {{}} promenna
# {% %} python 
# redirect pro post

user_reviews = {
    "pepa": "Hele fakt bomba website, ale chybi mi tu vlastne vsechno",
    "franta": "Chtel jsem najit recept na smazeny vajicka, ale dostal jsem se tu. Nevi jak.",
    "alena": "Produkt teto firmy je nejlepsi. Pouzivame ho vsichni. Obcas ho pujcime i dedeckovi."
}

@app.route("/")
@app.route("/home")
@app.route("/index")
def index():
    #kdykoliv někdo zažádá o endpoint index, tak se zvýší v Redis databázi záznam s klíčem homepage_requests o 1
    redis.incr("homepage_requests")
    counter = str(redis.get("homepage_requests"), "utf-8")
    #redis čítač pošleme do šablony index.html, kde ho následně jako Jinja2 proměnnou vypisujeme na obrazovku
    return render_template("index.html", reviews=user_reviews, view_count=counter)


@app.route("/review/<username>")
def get_review(username):
    if username in user_reviews:
        return f"Returning requested review. {username}: {user_reviews[username]}"
    else:
        return "Username not found in database."

@app.route("/datasets")
def datasets():
    mycollection = mydb["posts"]
    post = { "author": "Mike" }
    insertion = mycollection.insert_one(post)
    result = mycollection.find_one()
    return render_template("datasets.html", mongodb_test=result)

# POST - pro forms
@app.route("/contact", methods=["GET", "POST"])
def contact():
    query = "CREATE (n:Person {name: 'Alice'}) RETURN n"
    result = None
    with driver.session() as session:
        result = session.run(query)

    if request.method == "POST":
        # get("name")
        user_name = request.form.get("username")
        user_review = request.form.get("review")
        user_reviews[user_name] = user_review
    return render_template("contact.html", record=result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)