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

users_col    = db["users"]
projects_col = db["projects"]

# Ensure unique email index
users_col.create_index("email", unique=True)

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
    """Convert a MongoDB document (with _id ObjectId) to a plain dict."""
    if doc is None:
        return {}
    d = dict(doc)
    if "_id" in d:
        d["_id"] = str(d["_id"])
    return d


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
