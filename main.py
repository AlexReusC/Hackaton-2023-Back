from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import json_util
from bson.objectid import ObjectId
import json

app = Flask(__name__)
cluster =  MongoClient("mongodb://localhost:27017")
db = cluster["hackaton-2023"]

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
    popularhotels = list(collection.find().sort("calificacion", -1).limit(5))
    return json.loads(json_util.dumps(popularhotels)), 200

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

def fetch_establecimiento(id_establecimiento):
    collectionEstablecimientos = db["establecimientos"]
    return collectionEstablecimientos.find_one(ObjectId(id_establecimiento))

@app.route("/establecimiento/parametrosParaCalificar", methods=["GET"])
def get_parametros_a_calificar():
    id_establecimiento = request.args.get('id')
    return parametros_a_calificar(id_establecimiento), 200


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
