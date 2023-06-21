from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import json_util
from flask_cors import CORS
import os
from bson.objectid import ObjectId
import json
from flask_jwt_extended import create_access_token,get_jwt,get_jwt_identity, \
                               unset_jwt_cookies, jwt_required, JWTManager

app = Flask(__name__)

CORS(app)
app.config["JWT_SECRET_KEY"] = "please-remember-to-change-me"
jwt = JWTManager(app)

cluster =  MongoClient("mongodb://localhost:27017")
os.environ["PYTHONHASHSEED"] = "12345"
db = cluster["hackaton-2023"]

DISCAPACIDADES_TEXTOS = ['Silla de ruedas', 'Baston', 'Andadera', 'Muletas', 'Asistencia para la vista']

@app.route("/signup/", methods=["POST"])
def signup():
    collection = db["usuarios"]

    print(request.form["name"])    
    username = json.loads(request.form["name"])
    password = json.loads(request.form["password"])
    email = json.loads(request.form["email"])
    edad = json.loads(request.form["age"])
    discapacidad1 = json.loads(request.form["discapacidad1"])
    discapacidad2 = json.loads(request.form["discapacidad2"])
    discapacidad3 = json.loads(request.form["discapacidad3"])
    discapacidad4 = json.loads(request.form["discapacidad4"])
    discapacidad5 = json.loads(request.form["discapacidad5"])
    discapacidades = [discapacidad1, discapacidad2, discapacidad3, discapacidad4, discapacidad5]

    resultados = []
    for x in discapacidades:
        if x == True:
            resultados.append(1)
        else:
            resultados.append(0)

    

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


    if collection.count_documents({"nombre": username, "contrasena": hash(password)}) == 0:
        return jsonify({"message": "account doesnt exist"}), 400

    user = collection.find_one({"nombre": username, "contrasena": hash(password)})
    user_id = str(user["_id"])
    print(user_id)
    access_token = create_access_token(identity=user_id)
    return jsonify({"token": access_token}), 200

@app.route("/createhotel/", methods=["POST"])
@jwt_required()
def create_hotel():
    current_user = get_jwt_identity()
    print(current_user)
    #score = json.loads(request.form["score"])

    collection = db["establecimientos"]
    post = {"calificacion": 5, "tipo": 0}
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

def fetch_establecimiento(id_establecimiento):
    collectionEstablecimientos = db["establecimientos"]
    return collectionEstablecimientos.find_one(ObjectId(id_establecimiento))

def fetch_usuario(id_usuario):
    collectionUsuarios = db["usuarios"]
    return collectionUsuarios.find_one(ObjectId(id_usuario))


@app.route("/detalleEstablecimiento", methods=["GET"])
def detalle_establecimiento():
    id_establecimiento = request.args.get('id')
    establecimiento = fetch_establecimiento(id_establecimiento)
    print(establecimiento)
    print(type(establecimiento))
    return json.loads(json_util.dumps(establecimiento))

@app.route("/detalleUsuario", methods=["GET"])
@jwt_required()
def detalle_usuario():
    id_usuario = get_jwt_identity()
    print(id_usuario)
    usuario = fetch_usuario(id_usuario)
    print(usuario)
    print(type(usuario))
    discapacidades = usuario['discapacidades']
    discapacidades_textos = []
    for i in range(len(discapacidades)):
        if discapacidades[i] == 1:
            discapacidades_textos.append(DISCAPACIDADES_TEXTOS[i])
    usuario['discapacidades_textos'] = discapacidades_textos

    return json.loads(json_util.dumps(usuario))

def parametros_a_calificar(id_establecimiento):
    collectionEstablecimientos = db["establecimientos"]
    establecimientoResult =  collectionEstablecimientos.find_one(ObjectId(id_establecimiento))
    
    tipo_establecimiento = establecimientoResult['tipo']
    result = {
        'banos':2,
        'pasillos':2,
        'elevadores': int(establecimientoResult['elevadores']),
        'mascotas': int(establecimientoResult['mascotas']),
        'rampa': int(establecimientoResult['existencia_rampa']),
        'habitaciones': establecimientoResult['tipo'] #0 si, 1 no
    }
    return jsonify(result)

@app.route("/establecimiento/parametrosParaCalificar", methods=["GET"])
def get_parametros_a_calificar():
    id_establecimiento = request.args.get('id')
    guia = json.loads(parametros_a_calificar(id_establecimiento).get_data())
    print(guia)
    resultado = []
    if guia['rampa'] == 2:
        resultado.append('rampa')
    resultado.append('pasillo')
    if guia['habitaciones'] == 0:
        resultado.append('habitaciones')
    resultado.append('banos')
    return resultado, 200


@app.route("/establecimiento/calificar", methods=["POST"])
def post_calificar():
    """
    body of request = {
        id_establecimiento
        id_usuario
        calificacion_banos
        calificacion_pasillos
        calificacion_rampa * 
        calificacion_habitaciones *
        comentario
    }

    """
    ID_ESTABLECIMIENTO = "id_establecimiento"
    ID_USUARIO = "id_usuario"
    CAL_BANOS = "calificacion_banos"
    CAL_PASILLOS = "calificacion_pasillos"
    CAL_RAMPA = "calificacion_rampa"
    CAL_HABITACIONES = "calificacion_habitaciones"
    COMENTARIO = "comentario"
    N_CALIFICACIONES = "numero_calificaciones"
    CAL_ACCESIBILIDAD = "calificacion_accesibilidad"

    establecimiento = request.form[ID_ESTABLECIMIENTO]
    parametros_obligatorios = json.loads(parametros_a_calificar(establecimiento).get_data())
    usuario = request.form[ID_USUARIO]
    cal_banos = int(request.form[CAL_BANOS])
    cal_pasillos = int(request.form[CAL_PASILLOS])
    try:
        cal_rampa = json.loads(request.form[CAL_RAMPA])
        if parametros_obligatorios['rampa'] != 2:
            return "No se requeria calificacion para rampa", 400
    except KeyError:
        if parametros_obligatorios['rampa'] == 2:
            return "Se requeria calificacion para rampa", 400
        # No se requeria calificacion. Revisar si es porque no aplica, o porque no tiene
        cal_rampa = 0 if parametros_obligatorios['rampa'] == 0 else 5
    try:
        cal_habitaciones = json.loads(request.form[CAL_HABITACIONES])
        if parametros_obligatorios['habitaciones'] == 1:
            return "No se requeria calificacion para habitaciones", 400
    except KeyError:
        if parametros_obligatorios['habitaciones'] == 0:
            return "Se requeria calificacion para habitaciones", 400
        # No es hotel, se toma como 5 esa calificacion
        cal_habitaciones = 5
    try:
        comentario = str(request.form[COMENTARIO])
    except KeyError:
        comentario = None
    
    establecimiento_actual = fetch_establecimiento(establecimiento)
    actualizaciones_establecimiento = {}

    n_cal_establecimiento = establecimiento_actual[N_CALIFICACIONES] + 1
    actualizaciones_establecimiento[N_CALIFICACIONES] = n_cal_establecimiento

    actualizaciones_establecimiento[CAL_BANOS] = (establecimiento_actual[CAL_BANOS]*(n_cal_establecimiento-1) + cal_banos)/n_cal_establecimiento
    actualizaciones_establecimiento[CAL_PASILLOS] = (establecimiento_actual[CAL_PASILLOS]*(n_cal_establecimiento-1) + cal_pasillos)/n_cal_establecimiento
    # Se dio calificacion a rampa
    if parametros_obligatorios['rampa'] == 2:
        actualizaciones_establecimiento[CAL_RAMPA] = (establecimiento_actual[CAL_RAMPA]*(n_cal_establecimiento-1) + cal_rampa)/n_cal_establecimiento

    # Se dio calificacion a habitaciones
    if parametros_obligatorios['habitaciones'] == 0:
        actualizaciones_establecimiento[CAL_HABITACIONES] = (establecimiento_actual[CAL_HABITACIONES]*(n_cal_establecimiento-1) + cal_habitaciones)/n_cal_establecimiento

    peso_banos = 0.2 * cal_banos
    peso_pasillos = 0.2 * cal_pasillos
    peso_rampa = 0.2 * cal_rampa
    peso_habitaciones = 0.2 * cal_habitaciones

    peso_elevadores = 0
    peso_mascotas = 0
    # Si no es igual a 0, o no aplica o sí tiene elevador
    if parametros_obligatorios['elevadores'] != 0:
        peso_elevadores = 0.5
    if parametros_obligatorios['mascotas'] != 0:
        peso_mascotas = 0.5

    cal_final_usuario = peso_banos + peso_pasillos + peso_rampa + peso_habitaciones + peso_elevadores + peso_mascotas
    actualizaciones_establecimiento[CAL_ACCESIBILIDAD] = (establecimiento_actual[CAL_ACCESIBILIDAD]*(n_cal_establecimiento-1) + cal_final_usuario)/n_cal_establecimiento
    collectionEstablecimientos = db["establecimientos"]
    collectionEstablecimientos.update_one(
        {'_id': ObjectId(establecimiento)},
        {'$set':actualizaciones_establecimiento}
    )
    print(actualizaciones_establecimiento)
    
    resena = {
        'autor': usuario,
        'comentario':comentario,
        'calificaion_accesibilidad':cal_final_usuario,
    }

    collectionResenas = db["resenas"]
    print(collectionResenas.insert_one(resena))

    return "exito"

app.run()
