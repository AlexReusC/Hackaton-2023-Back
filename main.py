from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import json_util
import json

app = Flask(__name__)
#cluster = MongoClient("mongodb+srv://hackuser:q1VDRYnxE2XWj9xs@hackaton-2023.a5bw2x3.mongodb.net/?retryWrites=true&w=majority")
cluster =  MongoClient("mongodb://localhost:27017")
db = cluster["hackaton-2023"]
collection = db["establecimiento"]

@app.route("/createhotel/", methods=["POST"])
def create_hotel():
    score = json.loads(request.form["score"])

    collection = db["establecimientos"]
    post = {"calificacion": score, "tipo": 0}
    collection.insert_one(post)
    return jsonify(post), 201

@app.route("/popularhotel/", methods=["GET"])
def popularhotel():
    collection = db["establecimientos"]
    popularhotels = list(collection.find({"tipo": 0}).sort("calificacion_accesibilidad", -1).limit(5))
    return json.loads(json_util.dumps(popularhotels)), 200

@app.route("/popularrestaurante/", methods=["GET"])
def popularrestaurante():
    collection = db["establecimientos"]
    popularhotels = list(collection.find({"tipo": 1}).sort("calificacion_accesibilidad", -1).limit(5))
    return json.loads(json_util.dumps(popularhotels)), 200