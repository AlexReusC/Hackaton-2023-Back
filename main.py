from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import json_util
import os
import json
from flask_jwt_extended import create_access_token,get_jwt,get_jwt_identity, \
                               unset_jwt_cookies, jwt_required, JWTManager

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "please-remember-to-change-me"
jwt = JWTManager(app)

cluster =  MongoClient("mongodb://localhost:27017")
os.environ["PYTHONHASHSEED"] = "12345"
db = cluster["hackaton-2023"]
collection = db["establecimiento"]

@app.route("/createhotel/", methods=["POST"])
def create_hotel():
    score = json.loads(request.form["score"])

    collection = db["establecimientos"]
    post = {"calificacion": score, "tipo": 0}
    #collection.insert_one(post)
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

@app.route("/findstablishment/", methods=["GET"])
def findstablishment():
    collection = db["establecimientos"]
    name = request.args.get("name")

    popularhotels = list(collection.find({'$or': [
        {'nombre': {"$regex": name, "$options": "i"}},
        {'etiqueta_ubicación': {"$regex": name, "$options": "i"} }
    ]}))
    return json.loads(json_util.dumps(popularhotels)), 200

@app.route("/signup/", methods=["POST"])
def signup():
    collection = db["usuarios"]

    username = json.loads(request.form["username"])
    password = json.loads(request.form["password"])
    email = json.loads(request.form["email"])
    edad = json.loads(request.form["edad"])
    discapacidad1 = json.loads(request.form["discapacidad1"])
    discapacidad2 = json.loads(request.form["discapacidad2"])
    discapacidad3 = json.loads(request.form["discapacidad3"])
    discapacidad4 = json.loads(request.form["discapacidad4"])
    discapacidad5 = json.loads(request.form["discapacidad5"])
    discapacidades = [discapacidad1, discapacidad2, discapacidad3, discapacidad4, discapacidad5]

    mapping = {"true": 1, "false": 0}
    resultados = [mapping[elem] for elem in discapacidades]
    

    if collection.count_documents({"nombre": username}) > 0:
        return jsonify({"message": "username already exists"}), 400

    user = {"nombre": username, "email": email, "contrasena": hash(password), "edad": edad, "discapacidades": resultados}
    collection.insert_one(user)

    return json.loads(json_util.dumps(user)), 200

@app.route("/login/", methods=["POST"])
def login():
    collection = db["usuarios"]

    username = json.loads(request.form["username"])
    password = json.loads(request.form["password"])

    print(hash(password))

    if collection.count_documents({"nombre": username, "contrasena": hash(password)}) == 0:
        return jsonify({"message": "account doesnt exist"}), 400

    #user = collection.find({"nombre": username, "contrasena": hash(password)})
    access_token = create_access_token(identity=username)
    return jsonify(access_token), 200

