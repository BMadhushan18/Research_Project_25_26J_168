"""
Smart Construction Management - MongoDB Backend
Replaces Firebase/Firestore for all app operations.
Run:  python app.py
Port: 8090
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from bson.json_util import dumps
import bcrypt
import jwt
import datetime
import os
import json

app = Flask(__name__)
CORS(app)

# ─── Config ───────────────────────────────────────────────────────────────────
MONGO_URI  = "mongodb+srv://smartConstructiondb:admin123@smartconstructioncluste.fmhajos.mongodb.net/"
DB_NAME    = "smartConstructionDB"
JWT_SECRET = "scms_jwt_secret_2026_changeme"
JWT_EXPIRY_DAYS = 30
PORT       = 8090

# ─── MongoDB connection ────────────────────────────────────────────────────────
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
db     = client[DB_NAME]

users_col             = db["users"]
projects_col          = db["projects"]
threejs_col           = db["threejs"]
buildingstructure_col = db["buildingstructure"]
materials_col         = db["materials"]

# Ensure indexes
users_col.create_index("email", unique=True)
materials_col.create_index("name_lower")

# ─── Seed materials (runs at startup, drops + re-inserts so brand names stay correct) ─
_MAT_SEED = [
    # Foundation
    {"name":"Cement",                  "brands":["Lanwa","Sanstha"],                          "sizes":["25 kg","50 kg"]},
    {"name":"River Sand",              "brands":[],                                            "sizes":["Fine","Coarse","Washed"]},
    {"name":"Coarse Aggregate",        "brands":[],                                            "sizes":["10 mm","20 mm","40 mm"]},
    {"name":"Steel Rebar Y10",         "brands":["Taian"],                                     "sizes":["6 m","12 m"]},
    {"name":"Steel Rebar Y12",         "brands":["Taian"],                                     "sizes":["6 m","12 m"]},
    {"name":"Binding Wire",            "brands":[],                                            "sizes":["1 kg Roll","5 kg Roll"]},
    {"name":"Formwork Timber",         "brands":[],                                            "sizes":["1\"×4\"","2\"×4\"","2\"×6\""]},
    {"name":"Nails",                   "brands":[],                                            "sizes":["2\"","3\"","4\"","5\""]},
    # Masonry
    {"name":"Hollow Concrete Blocks",  "brands":[],                                            "sizes":["4\"","6\"","9\""]},
    {"name":"DPC Sheet",               "brands":[],                                            "sizes":["1 m wide","2 m wide"]},
    {"name":"Lintel Steel",            "brands":["Taian"],                                     "sizes":["Y10","Y12","Y16"]},
    # Roofing
    {"name":"Roofing Sheets",          "brands":[],                                            "sizes":["2.4 m","3 m","3.6 m"]},
    {"name":"Timber Rafters",          "brands":[],                                            "sizes":["3\"×2\"","4\"×2\""]},
    {"name":"Timber Purlins",          "brands":[],                                            "sizes":["2\"×2\"","3\"×2\""]},
    {"name":"Ridge Cap",               "brands":[],                                            "sizes":["Standard","Heavy"]},
    {"name":"Fascia Board",            "brands":[],                                            "sizes":["3 m","4.8 m"]},
    {"name":"Roofing Nails",           "brands":[],                                            "sizes":["65 mm","75 mm","90 mm"]},
    {"name":"Roof Screws",             "brands":[],                                            "sizes":["50 mm","75 mm"]},
    # Plastering
    {"name":"Fine Sand",               "brands":[],                                            "sizes":["Fine","Extra Fine"]},
    {"name":"Plasticizer",             "brands":[],                                            "sizes":["1 L","5 L","20 L"]},
    # Flooring
    {"name":"Floor Tiles",             "brands":["Rocell","Nitco"],                            "sizes":["30×30 cm","45×45 cm","60×60 cm","30×60 cm"]},
    {"name":"Tile Adhesive",           "brands":["Lanwa"],                                     "sizes":["5 kg Bag","20 kg Bag"]},
    {"name":"Sand",                    "brands":[],                                            "sizes":["Fine","Coarse","Washed"]},
    {"name":"Tile Grout",              "brands":[],                                            "sizes":["2 kg","5 kg","10 kg"]},
    {"name":"Skirting Tiles",          "brands":["Rocell"],                                    "sizes":["10×60 cm","10×45 cm"]},
    # Doors & Windows
    {"name":"Door Frames",             "brands":[],                                            "sizes":["2040×820 mm","2040×720 mm","2040×900 mm"]},
    {"name":"Door Leaves",             "brands":[],                                            "sizes":["820 mm","720 mm","900 mm"]},
    {"name":"Window Frames",           "brands":[],                                            "sizes":["600×600 mm","900×900 mm","1200×900 mm"]},
    {"name":"Window Glass",            "brands":[],                                            "sizes":["4 mm","6 mm","8 mm"]},
    {"name":"Hinges",                  "brands":[],                                            "sizes":["3\"","4\"","5\""]},
    {"name":"Door Locks",              "brands":[],                                            "sizes":["Standard","Heavy Duty"]},
    {"name":"Window Latches",          "brands":[],                                            "sizes":["Standard","Heavy"]},
    # Painting
    {"name":"Wall Paint (Interior)",   "brands":["Dulux","Causeway","Robbialac"],              "sizes":["1 L","4 L","20 L"]},
    {"name":"Ceiling Paint",           "brands":["Dulux","Causeway","Robbialac"],              "sizes":["1 L","4 L","20 L"]},
    {"name":"Exterior Paint",          "brands":["Dulux","Causeway","Robbialac"],              "sizes":["1 L","4 L","20 L"]},
    {"name":"Primer",                  "brands":["Dulux","Causeway"],                          "sizes":["1 L","4 L","20 L"]},
    {"name":"Wall Putty",              "brands":["Dulux","Causeway"],                          "sizes":["5 kg","10 kg","20 kg"]},
    {"name":"Paint Brushes / Rollers", "brands":[],                                            "sizes":["1\"","2\"","4\"","6\"","9\" Roller"]},
    # Electrical
    {"name":"PVC Conduit Pipe",        "brands":[],                                            "sizes":["20 mm","25 mm","32 mm"]},
    {"name":"Electrical Wire",         "brands":[],                                            "sizes":["1.5 mm²","2.5 mm²","4 mm²","6 mm²"]},
    {"name":"MCB Distribution Board",  "brands":[],                                            "sizes":["4 Way","8 Way","12 Way","16 Way"]},
    {"name":"Switches",                "brands":[],                                            "sizes":["1 Gang","2 Gang","3 Gang"]},
    {"name":"Electrical Sockets",      "brands":[],                                            "sizes":["Single","Double","Triple"]},
    {"name":"Light Fittings",          "brands":[],                                            "sizes":["E27","B22","GU10"]},
    {"name":"Junction Boxes",          "brands":[],                                            "sizes":["25 mm","32 mm"]},
    # Plumbing
    {"name":"PVC Pipes",               "brands":[],                                            "sizes":["½\"","¾\"","1\"","1¼\"","1½\"","2\""]},
    {"name":"PVC Fittings",            "brands":[],                                            "sizes":["½\"","¾\"","1\"","1½\""]},
    {"name":"Wash Basin",              "brands":[],                                            "sizes":["Standard","Large","Small"]},
    {"name":"WC Closet",               "brands":[],                                            "sizes":["Standard","Wall Hung"]},
    {"name":"Kitchen Sink",            "brands":[],                                            "sizes":["Single Bowl","Double Bowl"]},
    {"name":"Water Taps",              "brands":[],                                            "sizes":["½\"","¾\""]},
    {"name":"Shower Set",              "brands":[],                                            "sizes":["Standard","Handheld","Overhead"]},
    {"name":"Water Tank",              "brands":[],                                            "sizes":["500 L","1000 L","2000 L","5000 L"]},
]

def _seed_materials():
    now = datetime.datetime.utcnow().isoformat()
    materials_col.drop()
    materials_col.create_index("name_lower")
    docs = [{"name": d["name"], "name_lower": d["name"].lower(),
              "brands": d["brands"], "sizes": d["sizes"],
              "createdAt": now, "updatedAt": now} for d in _MAT_SEED]
    materials_col.insert_many(docs)
    print(f"[seed] Inserted {len(docs)} material records.")

_seed_materials()

# ─── Helpers ──────────────────────────────────────────────────────────────────
def make_token(uid: str) -> str:
    payload = {
        "uid": uid,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXPIRY_DAYS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_uid() -> str | None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    payload = verify_token(token)
    return payload["uid"] if payload else None


def bson_to_dict(doc) -> dict:
    """Recursively convert a MongoDB document to a JSON-safe plain dict."""
    if doc is None:
        return {}
    return _clean(doc)


def _clean(obj):
    from bson import ObjectId
    if isinstance(obj, dict):
        return {k: (_clean(v) if k != "_id" else str(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(i) for i in obj]
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj


def err(msg: str, code: int = 400):
    return jsonify({"error": msg}), code


# ─── Auth routes ──────────────────────────────────────────────────────────────
@app.route("/auth/signup", methods=["POST"])
def signup():
    body = request.json or {}
    email       = (body.get("email") or "").strip().lower()
    password    = (body.get("password") or "").strip()
    displayName = (body.get("displayName") or "").strip()

    if not email or not password:
        return err("email and password required")
    if len(password) < 6:
        return err("password must be at least 6 characters")

    # Check duplicate
    if users_col.find_one({"email": email}):
        return err("Email already in use", 409)

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    now = datetime.datetime.utcnow().isoformat()
    user_doc = {
        "email":       email,
        "displayName": displayName,
        "passwordHash": pw_hash,
        "createdAt":   now,
        "lastLoginAt": now,
        "role":        "user",
    }
    result = users_col.insert_one(user_doc)
    uid    = str(result.inserted_id)
    token  = make_token(uid)

    user_out = {
        "uid":         uid,
        "email":       email,
        "displayName": displayName,
        "createdAt":   now,
        "lastLoginAt": now,
    }
    return jsonify({"token": token, "user": user_out}), 201


@app.route("/auth/signin", methods=["POST"])
def signin():
    body     = request.json or {}
    email    = (body.get("email") or "").strip().lower()
    password = (body.get("password") or "").strip()

    if not email or not password:
        return err("email and password required")

    user = users_col.find_one({"email": email})
    if not user:
        return err("Invalid email or password", 401)

    if not bcrypt.checkpw(password.encode(), user["passwordHash"].encode()):
        return err("Invalid email or password", 401)

    uid = str(user["_id"])
    now = datetime.datetime.utcnow().isoformat()
    users_col.update_one({"_id": user["_id"]}, {"$set": {"lastLoginAt": now}})

    token = make_token(uid)
    user_out = {
        "uid":         uid,
        "email":       user.get("email", ""),
        "displayName": user.get("displayName", ""),
        "createdAt":   user.get("createdAt", ""),
        "lastLoginAt": now,
    }
    return jsonify({"token": token, "user": user_out}), 200


@app.route("/auth/me", methods=["GET"])
def me():
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    try:
        user = users_col.find_one({"_id": ObjectId(uid)})
    except Exception:
        return err("Invalid token", 401)
    if not user:
        return err("User not found", 404)
    user_out = {
        "uid":         str(user["_id"]),
        "email":       user.get("email", ""),
        "displayName": user.get("displayName", ""),
        "createdAt":   user.get("createdAt", ""),
        "lastLoginAt": user.get("lastLoginAt", ""),
    }
    return jsonify({"user": user_out}), 200


@app.route("/auth/reset-password", methods=["POST"])
def reset_password():
    # For local dev: just shows the new password in response (not a real email)
    body  = request.json or {}
    email = (body.get("email") or "").strip().lower()
    user  = users_col.find_one({"email": email})
    if not user:
        # Don't reveal if user exists
        return jsonify({"message": "If that email exists, a reset link was sent."}), 200
    return jsonify({"message": "If that email exists, a reset link was sent."}), 200


# ─── Projects CRUD ────────────────────────────────────────────────────────────
def find_project(pid: str, uid: str):
    """Look up a project by _id (ObjectId or UUID string) or projectId field."""
    try:
        doc = projects_col.find_one({"_id": ObjectId(pid), "ownerUid": uid})
        if doc:
            return doc
    except Exception:
        pass
    # Try as plain string _id or projectId
    doc = projects_col.find_one({"$or": [{"_id": pid}, {"projectId": pid}], "ownerUid": uid})
    return doc


@app.route("/projects", methods=["GET"])
def list_projects():
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    docs = list(projects_col.find({"ownerUid": uid}))
    return jsonify([bson_to_dict(d) for d in docs]), 200


@app.route("/projects", methods=["POST"])
def create_project():
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    body = request.json or {}
    body["ownerUid"]  = uid
    body["createdAt"] = datetime.datetime.utcnow().isoformat()
    body["updatedAt"] = datetime.datetime.utcnow().isoformat()
    # Use projectId as _id if provided (allows UUID keys)
    if "projectId" in body:
        body["_id"] = body["projectId"]
    result = projects_col.insert_one(body)
    body["_id"] = str(result.inserted_id)
    return jsonify(bson_to_dict(body)), 201


@app.route("/projects/<pid>", methods=["GET"])
def get_project(pid):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    doc = find_project(pid, uid)
    if not doc:
        return err("Project not found", 404)
    return jsonify(bson_to_dict(doc)), 200


@app.route("/projects/<pid>", methods=["PUT"])
def update_project(pid):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    body = request.json or {}
    body.pop("_id", None)
    body["updatedAt"] = datetime.datetime.utcnow().isoformat()
    doc = find_project(pid, uid)
    if not doc:
        return err("Project not found", 404)
    projects_col.update_one({"_id": doc["_id"]}, {"$set": body})
    return jsonify({"updated": True}), 200


@app.route("/projects/<pid>", methods=["DELETE"])
def delete_project(pid):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    doc = find_project(pid, uid)
    if not doc:
        return err("Project not found", 404)
    projects_col.delete_one({"_id": doc["_id"]})
    return jsonify({"deleted": True}), 200


# ─── Subcollection CRUD  /projects/<pid>/<sub> ────────────────────────────────
def get_sub_col(pid: str, sub: str):
    """Each project's subcollection stored as db['p_<pid_short>_<sub>']"""
    safe_pid = pid.replace("-", "")[:16]  # shorten UUID for collection name limit
    safe_sub = sub.replace("-", "_").replace("/", "_")
    return db[f"p_{safe_pid}_{safe_sub}"]


def find_sub_doc(col, doc_id: str, sub: str):
    """Find a sub-doc by MongoDB _id (ObjectId or UUID string) or model id field."""
    try:
        doc = col.find_one({"_id": ObjectId(doc_id)})
        if doc:
            return doc
    except Exception:
        pass
    # Try as string _id or common id field patterns
    doc = col.find_one({"_id": doc_id})
    if doc:
        return doc
    # Try model id field, e.g. 'materials' → 'materialId'
    singular = sub.rstrip('s')
    id_field = singular + 'Id'
    return col.find_one({id_field: doc_id})


@app.route("/projects/<pid>/<sub>", methods=["GET"])
def list_sub(pid, sub):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    col  = get_sub_col(pid, sub)
    docs = list(col.find())
    return jsonify([bson_to_dict(d) for d in docs]), 200


@app.route("/projects/<pid>/<sub>", methods=["POST"])
def create_sub(pid, sub):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    body = request.json or {}
    body["createdAt"] = datetime.datetime.utcnow().isoformat()
    col = get_sub_col(pid, sub)
    # Use custom id field as _id if present (e.g. materialId, workerId…)
    singular = sub.rstrip('s')
    id_field = singular + 'Id'
    if id_field in body:
        body["_id"] = body[id_field]
    result = col.insert_one(body)
    body["_id"] = str(result.inserted_id)
    return jsonify(bson_to_dict(body)), 201


@app.route("/projects/<pid>/<sub>/<doc_id>", methods=["GET"])
def get_sub_doc(pid, sub, doc_id):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    col = get_sub_col(pid, sub)
    doc = find_sub_doc(col, doc_id, sub)
    if not doc:
        return err("Not found", 404)
    return jsonify(bson_to_dict(doc)), 200


@app.route("/projects/<pid>/<sub>/<doc_id>", methods=["PUT"])
def update_sub_doc(pid, sub, doc_id):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    body = request.json or {}
    body.pop("_id", None)
    body["updatedAt"] = datetime.datetime.utcnow().isoformat()
    col = get_sub_col(pid, sub)
    doc = find_sub_doc(col, doc_id, sub)
    if not doc:
        return err("Not found", 404)
    col.update_one({"_id": doc["_id"]}, {"$set": body})
    return jsonify({"updated": True}), 200


@app.route("/projects/<pid>/<sub>/<doc_id>", methods=["DELETE"])
def delete_sub_doc(pid, sub, doc_id):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    col = get_sub_col(pid, sub)
    doc = find_sub_doc(col, doc_id, sub)
    if not doc:
        return err("Not found", 404)
    col.delete_one({"_id": doc["_id"]})
    return jsonify({"deleted": True}), 200


# ─── Building Structure endpoints ────────────────────────────────────────────
@app.route("/buildingstructure/<pid>", methods=["POST"])
def save_building_structure(pid):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    doc = find_project(pid, uid)
    if not doc:
        return err("Project not found", 404)
    body = request.json or {}
    print(f"[save_building_structure] pid={pid} uid={uid}")
    payload = {
        "projectId": pid,
        "ownerUid": uid,
        "data": body,
        "savedAt": datetime.datetime.utcnow().isoformat(),
    }
    # Upsert — one document per project in the shared buildingstructure collection
    buildingstructure_col.update_one(
        {"projectId": pid},
        {"$set": payload},
        upsert=True,
    )
    saved = buildingstructure_col.find_one({"projectId": pid})
    return jsonify(bson_to_dict(saved)), 200


@app.route("/buildingstructure/<pid>", methods=["GET"])
def get_building_structure(pid):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    saved = buildingstructure_col.find_one({"projectId": pid})
    if not saved:
        return jsonify({}), 200
    return jsonify(bson_to_dict(saved)), 200


# ─── ThreeJS per-project HTML routes ─────────────────────────────────────────
@app.route("/threejs/<project_id>", methods=["GET"])
def get_threejs(project_id):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)

    doc = threejs_col.find_one({"projectId": project_id, "ownerUid": uid})
    if not doc:
        # Fallback for legacy records saved with a different ownerUid.
        doc = threejs_col.find_one({"projectId": project_id})
    if not doc:
        return jsonify({
            "projectId": project_id,
            "foundation": None,
            "finishing": None,
        }), 200

    return jsonify({
        "projectId": project_id,
        "foundation": doc.get("foundation"),
        "finishing": doc.get("finishing"),
        "updatedAt": doc.get("updatedAt"),
    }), 200


@app.route("/threejs/<project_id>", methods=["POST"])
def upsert_threejs(project_id):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)

    body = request.json or {}
    now = datetime.datetime.utcnow().isoformat()

    update = {
        "projectId": project_id,
        "ownerUid": uid,
        "updatedAt": now,
    }
    if "foundation" in body:
        update["foundation"] = body.get("foundation")
    if "finishing" in body:
        update["finishing"] = body.get("finishing")

    threejs_col.update_one(
        {"projectId": project_id},
        {"$set": update, "$setOnInsert": {"createdAt": now}},
        upsert=True,
    )

    return jsonify({"ok": True, "projectId": project_id}), 200


@app.route("/threejs/<project_id>/<category>", methods=["GET"])
def get_threejs_category(project_id, category):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)

    if category not in ["foundation", "finishing"]:
        return err("category must be foundation or finishing", 400)

    doc = threejs_col.find_one({"projectId": project_id, "ownerUid": uid})
    if not doc:
        # Fallback for legacy records saved with a different ownerUid.
        doc = threejs_col.find_one({"projectId": project_id})
    if not doc:
        return jsonify({"html_code": None}), 200

    return jsonify({"html_code": doc.get(category)}), 200


@app.route("/threejs/<project_id>/<category>", methods=["POST"])
def set_threejs_category(project_id, category):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)

    if category not in ["foundation", "finishing"]:
        return err("category must be foundation or finishing", 400)

    body = request.json or {}
    html = body.get("html_code")
    now = datetime.datetime.utcnow().isoformat()

    threejs_col.update_one(
        {"projectId": project_id},
        {
            "$set": {
                "projectId": project_id,
                "ownerUid": uid,
                category: html,
                "updatedAt": now,
            },
            "$setOnInsert": {"createdAt": now},
        },
        upsert=True,
    )

    return jsonify({"ok": True, "projectId": project_id, "category": category}), 200


# ─── Materials library ────────────────────────────────────────────────────────

@app.route("/materials", methods=["GET"])
def list_materials():
    """Return all materials sorted by name."""
    docs = list(materials_col.find({}, {"_id": 1, "name": 1, "brands": 1, "sizes": 1})
                              .sort("name", 1))
    return jsonify([bson_to_dict(d) for d in docs]), 200


@app.route("/materials", methods=["POST"])
def create_material():
    """Create a new material.  Body: {name, brands:[...], sizes:[...]}"""
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    body   = request.json or {}
    name   = (body.get("name") or "").strip()
    if not name:
        return err("name is required")
    brands = [b.strip() for b in (body.get("brands") or []) if b.strip()]
    sizes  = [s.strip() for s in (body.get("sizes")  or []) if s.strip()]
    if materials_col.find_one({"name_lower": name.lower()}):
        return err(f"Material '{name}' already exists", 409)
    now = datetime.datetime.utcnow().isoformat()
    doc = {"name": name, "name_lower": name.lower(),
           "brands": brands, "sizes": sizes,
           "createdAt": now, "updatedAt": now}
    result = materials_col.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return jsonify(bson_to_dict(doc)), 201


@app.route("/materials/options/<path:material_name>", methods=["GET"])
def get_material_options(material_name):
    """Return brands and sizes for a material name (case-insensitive)."""
    doc = materials_col.find_one(
        {"name_lower": material_name.strip().lower()},
        {"_id": 0, "brands": 1, "sizes": 1}
    )
    if not doc:
        return jsonify({"brands": [], "sizes": []}), 200
    return jsonify({"brands": doc.get("brands", []),
                    "sizes":  doc.get("sizes",  [])}), 200


@app.route("/materials/<material_id>", methods=["GET"])
def get_material(material_id):
    """Get one material by MongoDB _id."""
    try:
        doc = materials_col.find_one({"_id": ObjectId(material_id)})
    except Exception:
        return err("Invalid id", 400)
    if not doc:
        return err("Not found", 404)
    return jsonify(bson_to_dict(doc)), 200


@app.route("/materials/<material_id>", methods=["PUT"])
def update_material(material_id):
    """Update name / brands / sizes.  Body: {name?, brands?:[...], sizes?:[...]}"""
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    body   = request.json or {}
    update = {"updatedAt": datetime.datetime.utcnow().isoformat()}
    if "brands" in body:
        update["brands"] = [b.strip() for b in body["brands"] if b.strip()]
    if "sizes" in body:
        update["sizes"]  = [s.strip() for s in body["sizes"]  if s.strip()]
    if "name" in body:
        n = body["name"].strip()
        if n:
            update["name"]       = n
            update["name_lower"] = n.lower()
    try:
        res = materials_col.update_one({"_id": ObjectId(material_id)}, {"$set": update})
    except Exception:
        return err("Invalid id", 400)
    if res.matched_count == 0:
        return err("Not found", 404)
    doc = materials_col.find_one({"_id": ObjectId(material_id)})
    return jsonify(bson_to_dict(doc)), 200


@app.route("/materials/<material_id>", methods=["DELETE"])
def delete_material(material_id):
    """Delete a material entry."""
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    try:
        res = materials_col.delete_one({"_id": ObjectId(material_id)})
    except Exception:
        return err("Invalid id", 400)
    if res.deleted_count == 0:
        return err("Not found", 404)
    return jsonify({"ok": True}), 200


# ─── Health check ─────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    try:
        client.admin.command("ping")
        return jsonify({"status": "ok", "db": DB_NAME, "mongo": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print(f"\nSmart Construction MongoDB Backend")
    print(f"   DB  : {DB_NAME}")
    print(f"   URL : http://0.0.0.0:{PORT}")
    print(f"   Health: http://localhost:{PORT}/health\n")
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
