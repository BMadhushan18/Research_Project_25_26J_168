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
import re
import math

app = Flask(__name__)
CORS(app)

# ─── Contour Detection Blueprint (bawanthaModel) ──────────────────────────────
from bawanthaModel.contour_routes import contour_bp
app.register_blueprint(contour_bp)

# ─── Comprehensive CV Analysis Blueprint ───────────────────────────────────
from bawanthaModel.comprehensive_cv_routes import comprehensive_cv_bp
app.register_blueprint(comprehensive_cv_bp)

# ─── Config ───────────────────────────────────────────────────────────────────
MONGO_URI  = os.getenv(
    "MONGO_URI",
    "mongodb+srv://smartConstructiondb:admin123@smartconstructioncluste.fmhajos.mongodb.net/"
)
DB_NAME    = os.getenv("MONGO_DB_NAME", "smartConstructionDB")
JWT_SECRET = "scms_jwt_secret_2026_changeme"
JWT_EXPIRY_DAYS = 30
PORT       = 8090
MONGO_TIMEOUT_MS = int(os.getenv("MONGO_TIMEOUT_MS", "10000"))

# ─── MongoDB connection ────────────────────────────────────────────────────────
client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=MONGO_TIMEOUT_MS,
    connectTimeoutMS=MONGO_TIMEOUT_MS,
    socketTimeoutMS=MONGO_TIMEOUT_MS,
)
db     = client[DB_NAME]

DB_READY = False
DB_INIT_ERROR = "Database init has not run yet."

users_col             = db["users"]
projects_col          = db["projects"]
threejs_col           = db["threejs"]
buildingstructure_col = db["buildingstructure"]
structuralframe_col   = db["structuralframe"]
walling_col           = db["walling"]
finishing_col         = db["finishing"]
materials_col         = db["materials"]
boqReport_col         = db["boqReport"]

# ─── Seed materials (runs at startup, drops + re-inserts so brand names stay correct) ─
# Schema: name, category, unit, sizes, brands, boqSections
_MAT_SEED = [
    # ── Concrete & Foundation ─────────────────────────────────────────────────
    {"name":"Cement (OPC)",             "category":"Concrete & Foundation", "unit":"bag",     "unitPrice":2200,
     "brands":["INSEE","Sanstha","Tokyo Cement","Holcim","Lanwa"],
     "sizes":["25 kg","50 kg"],
     "boqSections":["foundation","structural_frame","walling","plastering","flooring"]},
    {"name":"River Sand",               "category":"Concrete & Foundation", "unit":"m³",      "unitPrice":8500,
     "brands":[],
     "sizes":["Fine Grade","Coarse Grade","Washed"],
     "boqSections":["foundation","structural_frame","walling","plastering"]},
    {"name":"Coarse Aggregate",         "category":"Concrete & Foundation", "unit":"m³",      "unitPrice":12000,
     "brands":[],
     "sizes":["10 mm","20 mm","40 mm"],
     "boqSections":["foundation","structural_frame"]},
    {"name":"Fine Sand",                "category":"Concrete & Foundation", "unit":"m³",      "unitPrice":9000,
     "brands":[],
     "sizes":["Fine Grade","Extra Fine Grade"],
     "boqSections":["plastering","flooring"]},
    {"name":"Polythene Sheet",          "category":"Concrete & Foundation", "unit":"m²",      "unitPrice":85,
     "brands":[],
     "sizes":["125 µm (500 gauge)","250 µm (1000 gauge)"],
     "boqSections":["foundation","walling"]},
    # ── Structural Steel ──────────────────────────────────────────────────────
    {"name":"Steel Rebar Y10",          "category":"Structural Steel",      "unit":"kg",      "unitPrice":220,
     "brands":["Taian","Aruna Steel","Lanka Steel"],
     "sizes":["6 m length","12 m length"],
     "boqSections":["foundation","structural_frame","walling"]},
    {"name":"Steel Rebar Y12",          "category":"Structural Steel",      "unit":"kg",      "unitPrice":230,
     "brands":["Taian","Aruna Steel","Lanka Steel"],
     "sizes":["6 m length","12 m length"],
     "boqSections":["foundation","structural_frame"]},
    {"name":"Steel Rebar Y16",          "category":"Structural Steel",      "unit":"kg",      "unitPrice":245,
     "brands":["Taian","Aruna Steel","Lanka Steel"],
     "sizes":["6 m length","12 m length"],
     "boqSections":["structural_frame"]},
    {"name":"Steel Rebar Y20",          "category":"Structural Steel",      "unit":"kg",      "unitPrice":255,
     "brands":["Taian","Aruna Steel","Lanka Steel"],
     "sizes":["6 m length","12 m length"],
     "boqSections":["structural_frame","foundation"]},
    {"name":"Binding Wire",             "category":"Structural Steel",      "unit":"kg",      "unitPrice":380,
     "brands":[],
     "sizes":["1 kg roll","5 kg roll"],
     "boqSections":["foundation","structural_frame"]},
    {"name":"Mild Steel Nails",         "category":"Structural Steel",      "unit":"kg",      "unitPrice":420,
     "brands":[],
     "sizes":["2\" (50 mm)","3\" (75 mm)","4\" (100 mm)"],
     "boqSections":["structural_frame","roofing"]},
    # ── Masonry & Walling ─────────────────────────────────────────────────────
    {"name":"Hollow Concrete Blocks",   "category":"Masonry & Walling",     "unit":"No.",     "unitPrice":85,
     "brands":["Ranasinghe Bricks","Lanka Blocks","Premier Blocks"],
     "sizes":["4\" (100×200×400 mm)","6\" (150×200×400 mm)","9\" (230×200×400 mm)"],
     "boqSections":["walling"]},
    {"name":"Clay Bricks",              "category":"Masonry & Walling",     "unit":"No.",     "unitPrice":25,
     "brands":["Ranasinghe Bricks","Kandy Brick"],
     "sizes":["Standard (230×115×76 mm)","Modular (190×90×57 mm)"],
     "boqSections":["walling"]},
    {"name":"DPC Sheet",                "category":"Masonry & Walling",     "unit":"m",       "unitPrice":280,
     "brands":["Rhino","Lanka Poly"],
     "sizes":["100 mm wide","300 mm wide","600 mm wide"],
     "boqSections":["walling","foundation"]},
    {"name":"Lintel Steel Bar",         "category":"Masonry & Walling",     "unit":"kg",      "unitPrice":225,
     "brands":["Taian","Aruna Steel"],
     "sizes":["Y10 – 6 m","Y12 – 6 m","Y16 – 6 m"],
     "boqSections":["walling"]},
    # ── Plastering & Finishing ────────────────────────────────────────────────
    {"name":"Wall Putty",               "category":"Plastering & Finishing", "unit":"bag",    "unitPrice":1850,
     "brands":["Dulux","Causeway","Robbialac","Berger"],
     "sizes":["5 kg","10 kg","20 kg"],
     "boqSections":["plastering"]},
    {"name":"Plasticizer / Bond Coat",  "category":"Plastering & Finishing", "unit":"L",      "unitPrice":950,
     "brands":["SikaBond","Fosroc","Duraset"],
     "sizes":["1 L","5 L","20 L"],
     "boqSections":["plastering"]},
    {"name":"Skimcoat / Skim Plaster",  "category":"Plastering & Finishing", "unit":"bag",    "unitPrice":1650,
     "brands":["Dulux","Causeway","Diamond"],
     "sizes":["5 kg","20 kg","40 kg"],
     "boqSections":["plastering"]},
    # ── Flooring ─────────────────────────────────────────────────────────────
    {"name":"Floor Tiles",              "category":"Flooring",              "unit":"m²",      "unitPrice":1800,
     "brands":["Rocell","Nitco","Diamond","Asia Tiles","Euro Ceramics"],
     "sizes":["30×30 cm","45×45 cm","60×60 cm","30×60 cm","60×120 cm"],
     "boqSections":["flooring"]},
    {"name":"Tile Adhesive",            "category":"Flooring",              "unit":"bag",     "unitPrice":650,
     "brands":["Lanwa","Rocell Bond","MasterTile","SikaCeram"],
     "sizes":["5 kg bag","20 kg bag"],
     "boqSections":["flooring"]},
    {"name":"Tile Grout",               "category":"Flooring",              "unit":"kg",      "unitPrice":1200,
     "brands":["Lanwa","Rocell","SikaGrout"],
     "sizes":["2 kg","5 kg","10 kg"],
     "boqSections":["flooring"]},
    {"name":"Skirting Tiles",           "category":"Flooring",              "unit":"m",       "unitPrice":380,
     "brands":["Rocell","Diamond","Euro Ceramics"],
     "sizes":["10×60 cm","10×45 cm","10×30 cm"],
     "boqSections":["flooring"]},
    # ── Roofing ───────────────────────────────────────────────────────────────
    {"name":"Roofing Sheets (Zincalume)","category":"Roofing",              "unit":"m²",      "unitPrice":3500,
     "brands":["Lysaght Lanka","Steelco","Metecno"],
     "sizes":["0.47 mm BMT","0.55 mm BMT","0.60 mm BMT"],
     "boqSections":["roofing"]},
    {"name":"Roof Purlins / Timber",    "category":"Roofing",              "unit":"m",       "unitPrice":850,
     "brands":[],
     "sizes":["2\"×2\"","3\"×2\"","4\"×2\""],
     "boqSections":["roofing"]},
    {"name":"Ridge Cap",                "category":"Roofing",              "unit":"m",       "unitPrice":1200,
     "brands":["Lysaght Lanka","Steelco"],
     "sizes":["Standard","Heavy Duty"],
     "boqSections":["roofing"]},
    {"name":"Roofing Screws / Nails",   "category":"Roofing",              "unit":"No.",     "unitPrice":25,
     "brands":[],
     "sizes":["50 mm","65 mm","75 mm","90 mm"],
     "boqSections":["roofing"]},
    # ── Doors & Windows ───────────────────────────────────────────────────────
    {"name":"Door Frame (Hardwood)",    "category":"Doors & Windows",       "unit":"No.",     "unitPrice":18500,
     "brands":["Malwatte Wood","Timber Corp"],
     "sizes":["2040×820 mm","2040×720 mm","2040×900 mm"],
     "boqSections":["doors_windows"]},
    {"name":"Door Leaf (Flush/Panel)",  "category":"Doors & Windows",       "unit":"No.",     "unitPrice":22000,
     "brands":["Ridgewood","Millboard","Flexiwood"],
     "sizes":["820 mm","720 mm","900 mm"],
     "boqSections":["doors_windows"]},
    {"name":"Window Frame (Aluminium)", "category":"Doors & Windows",       "unit":"No.",     "unitPrice":28000,
     "brands":["Alumex","Aluline","Lanka Aluminium"],
     "sizes":["600×600 mm","900×900 mm","1200×900 mm","1500×1200 mm"],
     "boqSections":["doors_windows"]},
    {"name":"Window Glass",             "category":"Doors & Windows",       "unit":"m²",      "unitPrice":3200,
     "brands":["Pilkington","Saint-Gobain"],
     "sizes":["4 mm clear","6 mm clear","8 mm clear","6 mm tinted"],
     "boqSections":["doors_windows"]},
    {"name":"Door Locks / Handles",     "category":"Doors & Windows",       "unit":"No.",     "unitPrice":4500,
     "brands":["Godrej","Yale","Master Lock"],
     "sizes":["Standard Mortise","Heavy Duty","Digital Lock"],
     "boqSections":["doors_windows"]},
    # ── Paint & Coatings ──────────────────────────────────────────────────────
    {"name":"Wall Paint (Interior)",    "category":"Paint & Coatings",      "unit":"L",       "unitPrice":1050,
     "brands":["Dulux","Causeway","Robbialac","Berger","Nippon"],
     "sizes":["1 L","4 L","20 L"],
     "boqSections":["painting"]},
    {"name":"Ceiling Paint",            "category":"Paint & Coatings",      "unit":"L",       "unitPrice":900,
     "brands":["Dulux","Causeway","Robbialac"],
     "sizes":["1 L","4 L","20 L"],
     "boqSections":["painting"]},
    {"name":"Exterior Paint",           "category":"Paint & Coatings",      "unit":"L",       "unitPrice":1350,
     "brands":["Dulux Weathershield","Causeway Exterior","Robbialac"],
     "sizes":["1 L","4 L","20 L"],
     "boqSections":["painting"]},
    {"name":"Primer (Alkali Resistant)","category":"Paint & Coatings",      "unit":"L",       "unitPrice":680,
     "brands":["Dulux","Causeway","Berger"],
     "sizes":["1 L","4 L","20 L"],
     "boqSections":["painting"]},
    {"name":"Paint Brushes / Rollers",  "category":"Paint & Coatings",      "unit":"No.",     "unitPrice":350,
     "brands":["Jaybee","Nippon"],
     "sizes":["1\"","2\"","4\"","6\"","9\" Roller"],
     "boqSections":["painting"]},
    # ── Electrical ────────────────────────────────────────────────────────────
    {"name":"PVC Conduit Pipe",         "category":"Electrical",            "unit":"m",       "unitPrice":185,
     "brands":["Supreme","Kandy Plastics","Duraline"],
     "sizes":["20 mm dia","25 mm dia","32 mm dia"],
     "boqSections":["electrical"]},
    {"name":"Electrical Wire (PVC)",    "category":"Electrical",            "unit":"m",       "unitPrice":120,
     "brands":["Met-Lanka","CML","Wellcab"],
     "sizes":["1.5 mm²","2.5 mm²","4 mm²","6 mm²"],
     "boqSections":["electrical"]},
    {"name":"MCB Distribution Board",   "category":"Electrical",            "unit":"No.",     "unitPrice":6500,
     "brands":["Schneider","ABB","Legrand","Hager"],
     "sizes":["4 Way","8 Way","12 Way","16 Way","24 Way"],
     "boqSections":["electrical"]},
    {"name":"Switches",                 "category":"Electrical",            "unit":"No.",     "unitPrice":350,
     "brands":["Vinton","SL Switches","Anchor"],
     "sizes":["1 Gang","2 Gang","3 Gang"],
     "boqSections":["electrical"]},
    {"name":"Electrical Sockets",       "category":"Electrical",            "unit":"No.",     "unitPrice":480,
     "brands":["Vinton","MK","Anchor"],
     "sizes":["Single (3-pin)","Double (3-pin)","Triple"],
     "boqSections":["electrical"]},
    {"name":"Light Fittings (LED)",     "category":"Electrical",            "unit":"No.",     "unitPrice":850,
     "brands":["Philips","Osram","LifeLight"],
     "sizes":["E27 Bulb Holder","B22 Batten","GU10 Spot","Batten (1200 mm)"],
     "boqSections":["electrical"]},
    # ── Plumbing ──────────────────────────────────────────────────────────────
    {"name":"uPVC Pressure Pipes",      "category":"Plumbing",              "unit":"m",       "unitPrice":180,
     "brands":["Kandy Plastics","Amanco","Supreme"],
     "sizes":["½\" (15 mm)","¾\" (20 mm)","1\" (25 mm)","1½\" (40 mm)","2\" (50 mm)"],
     "boqSections":["plumbing"]},
    {"name":"PVC Fittings (Elbows/Tees)","category":"Plumbing",             "unit":"No.",     "unitPrice":95,
     "brands":["Kandy Plastics","Amanco"],
     "sizes":["½\"","¾\"","1\"","1½\""],
     "boqSections":["plumbing"]},
    {"name":"Wash Basin",               "category":"Plumbing",              "unit":"No.",     "unitPrice":18000,
     "brands":["American Standard","Kohler","Duravit"],
     "sizes":["Standard 500×400 mm","Large 600×450 mm"],
     "boqSections":["plumbing"]},
    {"name":"WC Closet",                "category":"Plumbing",              "unit":"No.",     "unitPrice":32000,
     "brands":["American Standard","Kohler","Duravit"],
     "sizes":["Standard","Wall Hung","Short Projection"],
     "boqSections":["plumbing"]},
    {"name":"Kitchen Sink (Stainless)", "category":"Plumbing",              "unit":"No.",     "unitPrice":28000,
     "brands":["Futura","Anex","Jayna"],
     "sizes":["Single Bowl (450×400 mm)","Double Bowl (800×400 mm)"],
     "boqSections":["plumbing"]},
    {"name":"Water Taps (Brass/Chrome)","category":"Plumbing",              "unit":"No.",     "unitPrice":2500,
     "brands":["Multitap","Futura","Kohler"],
     "sizes":["½\" pillar","½\" bib","¾\" bib"],
     "boqSections":["plumbing"]},
    {"name":"Water Tank (PVC/HDPE)",    "category":"Plumbing",              "unit":"No.",     "unitPrice":45000,
     "brands":["Panseal","Rhino","Arpico"],
     "sizes":["500 L","1000 L","2000 L","5000 L"],
     "boqSections":["plumbing"]},
    # ── Anti-Termite / Misc ───────────────────────────────────────────────────
    {"name":"Anti-Termite Treatment",   "category":"Ironmongery & Misc",    "unit":"L",       "unitPrice":2800,
     "brands":["Termidor","Chlorpyrifos"],
     "sizes":["1 L","5 L"],
     "boqSections":["foundation"]},
]

def _seed_materials():
    now = datetime.datetime.utcnow().isoformat()
    materials_col.drop()
    materials_col.create_index("name_lower")
    docs = [
        {
            "name":        d["name"],
            "name_lower":  d["name"].lower(),
            "category":    d.get("category", "General"),
            "unit":        d.get("unit", "No."),
            "unitPrice":   d.get("unitPrice"),
            "brands":      d.get("brands", []),
            "sizes":       d.get("sizes", []),
            "boqSections": d.get("boqSections", []),
            "createdAt":   now,
            "updatedAt":   now,
        }
        for d in _MAT_SEED
    ]
    materials_col.insert_many(docs)
    print(f"[seed] Inserted {len(docs)} material records.")


def _init_db() -> None:
    """Initialize Mongo indexes/seed once at startup with clear diagnostics."""
    global DB_READY, DB_INIT_ERROR
    try:
        client.admin.command("ping")
        users_col.create_index("email", unique=True)
        materials_col.create_index("name_lower")
        boqReport_col.create_index([("projectId", 1)], unique=True)
        _seed_materials()
        DB_READY = True
        DB_INIT_ERROR = ""
        print("[db] MongoDB connected and initialized.")
    except Exception as e:
        DB_READY = False
        DB_INIT_ERROR = str(e)
        print("[db] MongoDB initialization failed:")
        print(f"[db] {DB_INIT_ERROR}")


_init_db()

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


# ─── Structural Frame endpoints ───────────────────────────────────────────────
@app.route("/structuralframe/<pid>", methods=["POST"])
def save_structural_frame(pid):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    doc = find_project(pid, uid)
    if not doc:
        return err("Project not found", 404)
    body = request.json or {}
    print(f"[save_structural_frame] pid={pid} uid={uid}")
    payload = {
        "projectId": pid,
        "ownerUid": uid,
        "data": body,
        "savedAt": datetime.datetime.utcnow().isoformat(),
    }
    structuralframe_col.update_one(
        {"projectId": pid},
        {"$set": payload},
        upsert=True,
    )
    saved = structuralframe_col.find_one({"projectId": pid})
    return jsonify(bson_to_dict(saved)), 200


@app.route("/structuralframe/<pid>", methods=["GET"])
def get_structural_frame(pid):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    saved = structuralframe_col.find_one({"projectId": pid})
    if not saved:
        return jsonify({}), 200
    return jsonify(bson_to_dict(saved)), 200


# ─── Walling endpoints ────────────────────────────────────────────────────────
@app.route("/walling/<pid>", methods=["POST"])
def save_walling(pid):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    doc = find_project(pid, uid)
    if not doc:
        return err("Project not found", 404)
    body = request.json or {}
    print(f"[save_walling] pid={pid} uid={uid}")
    payload = {
        "projectId": pid,
        "ownerUid": uid,
        "data": body,
        "savedAt": datetime.datetime.utcnow().isoformat(),
    }
    walling_col.update_one(
        {"projectId": pid},
        {"$set": payload},
        upsert=True,
    )
    saved = walling_col.find_one({"projectId": pid})
    return jsonify(bson_to_dict(saved)), 200


@app.route("/walling/<pid>", methods=["GET"])
def get_walling(pid):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    saved = walling_col.find_one({"projectId": pid})
    if not saved:
        return jsonify({}), 200
    return jsonify(bson_to_dict(saved)), 200


# ─── Finishing endpoints ──────────────────────────────────────────────────────
@app.route("/finishing/<pid>", methods=["POST"])
def save_finishing(pid):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    doc = find_project(pid, uid)
    if not doc:
        return err("Project not found", 404)
    body = request.json or {}
    print(f"[save_finishing] pid={pid} uid={uid}")
    payload = {
        "projectId": pid,
        "ownerUid": uid,
        "data": body,
        "savedAt": datetime.datetime.utcnow().isoformat(),
    }
    finishing_col.update_one(
        {"projectId": pid},
        {"$set": payload},
        upsert=True,
    )
    saved = finishing_col.find_one({"projectId": pid})
    return jsonify(bson_to_dict(saved)), 200


@app.route("/finishing/<pid>", methods=["GET"])
def get_finishing(pid):
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)
    saved = finishing_col.find_one({"projectId": pid})
    if not saved:
        return jsonify({}), 200
    return jsonify(bson_to_dict(saved)), 200


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


# ─── BOQ computation ─────────────────────────────────────────────────────────

def _dim_to_m(raw, fallback=0.0):
    """Convert a raw dimension value (number or string with unit suffix) to metres."""
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw or '').strip().lower()
    if not text:
        return fallback
    m = re.search(r'-?\d+(?:\.\d+)?', text)
    if not m:
        return fallback
    val = float(m.group())
    if 'mm' in text:  return val / 1000
    if 'cm' in text:  return val / 100
    if 'ft' in text:  return val * 0.3048
    if 'in' in text:  return val * 0.0254
    return val


def _area_to_m2(raw):
    """Convert a raw area value to m²."""
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw or '').strip().lower()
    if not text:
        return 0.0
    m = re.search(r'\d+(?:\.\d+)?', text)
    if not m:
        return 0.0
    val = float(m.group())
    if 'sq ft' in text or 'ft²' in text or 'ft2' in text:
        return val * 0.092903
    return val


def _mat_info(mats_by_name, mat_name):
    """Return (brand, size) for a material from the cache (name_lower → doc)."""
    doc = mats_by_name.get(mat_name.lower())
    if not doc:
        return ('—', '—')
    brands = doc.get('brands', [])
    sizes  = doc.get('sizes',  [])
    return (brands[0] if brands else '—', sizes[0] if sizes else '—')


def _boq_row(mat_name, unit, qty, size, brand):
    return {'materialName': mat_name, 'unit': unit, 'quantity': qty, 'size': size, 'brand': brand}


def _extract_walling_m(doc):
    if not doc:
        return {'count': 0, 'total_length': 0.0, 'total_area': 0.0, 'total_volume': 0.0}
    data = doc.get('data', doc)
    gf   = data.get('groundFloor') if isinstance(data, dict) else None
    walls = gf.get('walls') if isinstance(gf, dict) else None
    if not walls or not isinstance(walls, dict):
        return {'count': 0, 'total_length': 0.0, 'total_area': 0.0, 'total_volume': 0.0}
    count, total_l, total_a, total_v = 0, 0.0, 0.0, 0.0
    for wall in walls.values():
        if not isinstance(wall, dict): continue
        l = _dim_to_m(wall.get('length'), 0)
        h = _dim_to_m(wall.get('height'), 0)
        t = _dim_to_m(wall.get('width'),  0.115)
        if l <= 0 or h <= 0: continue
        count   += 1
        total_l += l
        total_a += l * h
        total_v += l * h * t
    return {'count': count, 'total_length': total_l, 'total_area': total_a, 'total_volume': total_v}


def _extract_column_m(doc):
    if not doc:
        return {'count': 0, 'total_volume': 0.0, 'formwork_area': 0.0}
    data = doc.get('data', doc)
    gf   = data.get('groundFloor') if isinstance(data, dict) else None
    cols = gf.get('columns') if isinstance(gf, dict) else None
    if not cols or not isinstance(cols, dict):
        return {'count': 0, 'total_volume': 0.0, 'formwork_area': 0.0}
    count, total_v, fw_a = 0, 0.0, 0.0
    for col in cols.values():
        if not isinstance(col, dict): continue
        w = _dim_to_m(col.get('width'),  0.225)
        d = _dim_to_m(col.get('length'), 0.225)
        h = _dim_to_m(col.get('height'), 0)
        if h <= 0: continue
        count   += 1
        total_v += w * d * h
        fw_a    += 2 * (w + d) * h
    return {'count': count, 'total_volume': total_v, 'formwork_area': fw_a}


def _extract_floor_area(doc):
    if not doc: return 0.0
    data   = doc.get('data', doc)
    output = data.get('output') if isinstance(data, dict) else None
    raw    = output.get('floorAreaReported') if isinstance(output, dict) else None
    return _area_to_m2(raw)


def _boq_foundation(wall_m, col_m, floor_area, mats):
    rows = []
    eff_l = wall_m['total_length']
    if eff_l <= 0 and floor_area > 0:
        eff_l = math.sqrt(floor_area) * 4

    fc_vol = (eff_l * 0.60 * 0.25) + (col_m['count'] * 0.60 * 0.60 * 0.30)
    if fc_vol > 0.01:
        fc = fc_vol * 1.10  # 10 % wastage
        # Grade 25 (1:2:4) — 7.5 bags/m³ cement, 0.44 m³ sand, 0.88 m³ aggregate
        b, s = _mat_info(mats, 'Cement (OPC)')
        rows.append(_boq_row('Cement (OPC)',      'bag', float(max(1, round(fc * 7.5))),  s or '50 kg',      b or 'INSEE'))
        rows.append(_boq_row('River Sand',         'm³',  round(fc * 0.44, 2),             'Coarse Grade',    '—'))
        rows.append(_boq_row('Coarse Aggregate',   'm³',  round(fc * 0.88, 2),             '20 mm',           '—'))

    # Reinforcement — Y12 main bars + Y10 links
    steel_kg = eff_l * 2 * 0.888 + col_m['count'] * 4 * 0.60 * 0.888
    if steel_kg > 0.1:
        b12, s12 = _mat_info(mats, 'Steel Rebar Y12')
        b10, s10 = _mat_info(mats, 'Steel Rebar Y10')
        bw_b, bw_s = _mat_info(mats, 'Binding Wire')
        links_kg = steel_kg * 0.15
        rows.append(_boq_row('Steel Rebar Y12', 'kg', round(steel_kg, 1),              s12 or '12 m length', b12 or 'Taian'))
        rows.append(_boq_row('Steel Rebar Y10', 'kg', round(links_kg, 1),              s10 or '12 m length', b10 or 'Taian'))
        rows.append(_boq_row('Binding Wire',    'kg', round((steel_kg + links_kg) * 0.01, 2), bw_s or '1 kg roll', bw_b or '—'))

    # DPC / polythene sheet under footing
    dpm_a = eff_l * 0.70
    if dpm_a > 0.5:
        rows.append(_boq_row('Polythene Sheet', 'm²', round(dpm_a, 1), '250 µm (1000 gauge)', '—'))
    return rows


def _boq_structural(col_m, mats):
    rows = []
    if col_m['total_volume'] <= 0.01:
        return rows
    cv = col_m['total_volume'] * 1.10  # 10 % wastage
    # Grade 30 (1:1.5:3) — 8.2 bags/m³ cement, 0.41 m³ sand, 0.82 m³ aggregate
    b, s = _mat_info(mats, 'Cement (OPC)')
    rows.append(_boq_row('Cement (OPC)',    'bag', float(max(1, round(cv * 8.2))),  s or '50 kg', b or 'INSEE'))
    rows.append(_boq_row('River Sand',      'm³',  round(cv * 0.41, 2),             'Coarse Grade', '—'))
    rows.append(_boq_row('Coarse Aggregate','m³',  round(cv * 0.82, 2),             '20 mm',        '—'))

    main_kg = round(col_m['total_volume'] * 100, 1)
    link_kg = round(col_m['total_volume'] * 20,  1)
    b16, s16 = _mat_info(mats, 'Steel Rebar Y16')
    b10, s10 = _mat_info(mats, 'Steel Rebar Y10')
    bw_b, bw_s = _mat_info(mats, 'Binding Wire')
    if main_kg > 0.1:
        rows.append(_boq_row('Steel Rebar Y16', 'kg', main_kg, s16 or '12 m length', b16 or 'Taian'))
    if link_kg > 0.1:
        rows.append(_boq_row('Steel Rebar Y10', 'kg', link_kg, s10 or '12 m length', b10 or 'Taian'))
    total_steel = main_kg + link_kg
    if total_steel > 0.1:
        rows.append(_boq_row('Binding Wire', 'kg', round(total_steel * 0.01, 2), bw_s or '1 kg roll', bw_b or '—'))

    fw = col_m['formwork_area']
    if fw > 0.1:
        rows.append(_boq_row('Formwork Timber', 'm²', round(fw, 1), '¾" Plywood (8×4 ft)', '—'))
        rows.append(_boq_row('Mild Steel Nails', 'kg', round(fw * 0.15, 1), '3" (75 mm)', '—'))
    return rows


def _boq_walling(wall_m, mats):
    rows = []
    if wall_m['total_area'] <= 0.01:
        return rows
    wa = wall_m['total_area']
    wv = wall_m['total_volume']
    wl = wall_m['total_length']

    # 6" hollow concrete blocks: 12.5 No./m² (face area), 5 % wastage
    blocks = max(1, round(wa * 12.5 * 1.05))
    bk_b, bk_s = _mat_info(mats, 'Hollow Concrete Blocks')
    rows.append(_boq_row('Hollow Concrete Blocks', 'No.', float(blocks),
                          bk_s or '6" (150×200×400 mm)', bk_b or '—'))

    # Wall mortar (1:4) — 0.30 m³ mortar per m³ wall
    m_vol = wv * 0.30
    if m_vol > 0.01:
        b_c, s_c = _mat_info(mats, 'Cement (OPC)')
        rows.append(_boq_row('Cement (OPC) – Wall Mortar', 'bag',
                              float(max(1, round(m_vol * 5))), s_c or '50 kg', b_c or 'INSEE'))
        rows.append(_boq_row('River Sand – Wall Mortar', 'm³',
                              round(m_vol * 1.0, 2), 'Fine Grade', '—'))

    # DPC sheet at base of wall
    if wl > 0.5:
        dpc_b, dpc_s = _mat_info(mats, 'DPC Sheet')
        rows.append(_boq_row('DPC Sheet', 'm', round(wl, 1),
                              dpc_s or '300 mm wide', dpc_b or 'Rhino'))

    # Plaster (1:4 mix, 15 mm thick, both sides)
    p_area = wa * 2.0
    p_vol  = p_area * 0.015
    b_c, s_c = _mat_info(mats, 'Cement (OPC)')
    fs_b, fs_s = _mat_info(mats, 'Fine Sand')
    rows.append(_boq_row('Cement (OPC) – Plaster', 'bag',
                          float(max(1, round(p_vol * 5))), s_c or '50 kg', b_c or 'INSEE'))
    rows.append(_boq_row('Fine Sand – Plaster', 'm³',
                          round(p_vol, 2), fs_s or 'Fine Grade', fs_b or '—'))

    # Wall putty (0.5 kg/m², 5 kg bags)
    wp_bags = max(1, round(p_area * 0.5 / 5))
    wp_b, wp_s = _mat_info(mats, 'Wall Putty')
    rows.append(_boq_row('Wall Putty', 'bag', float(wp_bags),
                          wp_s or '5 kg', wp_b or 'Dulux'))
    return rows


def _boq_flooring(floor_area, mats):
    rows = []
    if floor_area <= 0.1:
        return rows
    t_b, t_s = _mat_info(mats, 'Floor Tiles')
    rows.append(_boq_row('Floor Tiles', 'm²', round(floor_area * 1.05, 1),
                          t_s or '60×60 cm', t_b or 'Rocell'))
    adh_b, adh_s = _mat_info(mats, 'Tile Adhesive')
    rows.append(_boq_row('Tile Adhesive', 'bag',
                          float(max(1, math.ceil(floor_area / 5))),
                          adh_s or '20 kg bag', adh_b or 'Lanwa'))
    tg_b, tg_s = _mat_info(mats, 'Tile Grout')
    rows.append(_boq_row('Tile Grout', 'kg', round(floor_area * 0.3, 1),
                          tg_s or '5 kg', tg_b or 'Lanwa'))
    return rows


@app.route("/boq/<pid>", methods=["GET"])
def get_boq(pid):
    """Compute, enrich with prices, persist to boqReport, and return the full BOQ."""
    uid = get_current_uid()
    if not uid:
        return err("Unauthorized", 401)

    bs_doc = buildingstructure_col.find_one({"projectId": pid})
    sf_doc = structuralframe_col.find_one({"projectId": pid})
    wa_doc = walling_col.find_one({"projectId": pid})

    # Materials lookup cache including unitPrice
    mat_docs = list(materials_col.find(
        {}, {"_id": 0, "name": 1, "name_lower": 1, "brands": 1, "sizes": 1, "unitPrice": 1}
    ))
    mats      = {d.get('name_lower', d.get('name', '').lower()): d for d in mat_docs}
    mat_prices = {
        d.get('name_lower', d.get('name', '').lower()): float(d.get('unitPrice') or 0)
        for d in mat_docs
    }

    wall_m = _extract_walling_m(wa_doc)
    col_m  = _extract_column_m(sf_doc)
    fa     = _extract_floor_area(bs_doc)

    has_data = (wall_m['total_area'] > 0 or col_m['total_volume'] > 0 or fa > 0)
    if not has_data:
        return jsonify({
            "sections": [],
            "hasData": False,
            "message": "No extracted measurement data found for this project. "
                       "Please extract plan measurements first.",
        }), 200

    sections = []
    f_rows = _boq_foundation(wall_m, col_m, fa, mats)
    if f_rows:
        sections.append({"section": "Foundation", "rows": f_rows})

    s_rows = _boq_structural(col_m, mats)
    if s_rows:
        sections.append({"section": "Structural Frame", "rows": s_rows})

    w_rows = _boq_walling(wall_m, mats)
    if w_rows:
        sections.append({"section": "Walling", "rows": w_rows})

    fl_rows = _boq_flooring(fa, mats)
    if fl_rows:
        sections.append({"section": "Flooring", "rows": fl_rows})

    # ── Enrich rows: add unitPrice + totalMaterialCost per row, section totals ─────
    grand_total = 0.0
    for sec in sections:
        sec_total = 0.0
        for row in sec['rows']:
            # Strip variant suffix e.g. "Cement (OPC) – Wall Mortar" → "Cement (OPC)"
            base_name = row['materialName'].split('–')[0].strip().split('—')[0].strip()
            up   = mat_prices.get(base_name.lower(), 0.0)
            cost = round((row.get('quantity') or 0) * up, 2)
            row['unitPrice']         = up
            row['totalMaterialCost'] = cost
            sec_total += cost
        sec['sectionTotal'] = round(sec_total, 2)
        grand_total += sec_total
    grand_total = round(grand_total, 2)

    metrics = {
        "wallCount":       wall_m['count'],
        "totalWallLength": round(wall_m['total_length'], 2),
        "totalWallArea":   round(wall_m['total_area'],   2),
        "columnCount":     col_m['count'],
        "totalColVolume":  round(col_m['total_volume'],  2),
        "floorArea":       round(fa, 2),
    }

    # ── Upsert to boqReport collection ──────────────────────────────────────────────
    now = datetime.datetime.utcnow().isoformat()
    boqReport_col.update_one(
        {"projectId": pid},
        {
            "$set": {
                "projectId":  pid,
                "sections":   sections,
                "grandTotal": grand_total,
                "metrics":    metrics,
                "hasData":    True,
                "updatedAt":  now,
            },
            "$setOnInsert": {"createdAt": now},
        },
        upsert=True,
    )

    return jsonify({
        "sections":   sections,
        "hasData":    True,
        "grandTotal": grand_total,
        "metrics":    metrics,
    }), 200


# ─── Materials library ────────────────────────────────────────────────────────

@app.route("/materials", methods=["GET"])
def list_materials():
    """Return all materials sorted by name."""
    docs = list(materials_col.find(
        {},
        {"_id": 1, "name": 1, "category": 1, "unit": 1, "unitPrice": 1, "brands": 1, "sizes": 1, "boqSections": 1}
    ).sort("name", 1))
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
    brands     = [b.strip() for b in (body.get("brands") or []) if b.strip()]
    sizes      = [s.strip() for s in (body.get("sizes")  or []) if s.strip()]
    category   = (body.get("category") or "General").strip()
    unit       = (body.get("unit") or "No.").strip()
    unit_price = body.get("unitPrice")
    if materials_col.find_one({"name_lower": name.lower()}):
        return err(f"Material '{name}' already exists", 409)
    now = datetime.datetime.utcnow().isoformat()
    doc = {"name": name, "name_lower": name.lower(),
           "category": category, "unit": unit,
           "unitPrice": unit_price,
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
        return jsonify({
            "status": "ok",
            "db": DB_NAME,
            "mongo": "connected",
            "dbReady": DB_READY,
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "db": DB_NAME,
            "mongo": "disconnected",
            "dbReady": DB_READY,
            "detail": str(e),
            "startupError": DB_INIT_ERROR,
        }), 500


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print(f"\nSmart Construction MongoDB Backend")
    print(f"   DB  : {DB_NAME}")
    print(f"   URL : http://0.0.0.0:{PORT}")
    print(f"   Health: http://localhost:{PORT}/health\n")
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
