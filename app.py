from flask import Flask, jsonify, request
from database import init_db, get_db

app = Flask(__name__)

app.secret_key = "civicai-secret-key"


@app.route("/")
def home():
    return "CivicAI Backend is running! 🚀"


@app.route("/api/health")
def health():
    return jsonify({
        "status": "success",
        "message": "CivicAI API is working"
    })


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({
            "status": "error",
            "message": "Name, email and password are required"
        }), 400

    conn = get_db()

    try:
        conn.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
            """,
            (name, email, password)
        )

        conn.commit()

        return jsonify({
            "status": "success",
            "message": "User registered successfully"
        }), 201

    except Exception:
        return jsonify({
            "status": "error",
            "message": "Email already registered"
        }), 409

    finally:
        conn.close()

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "status": "error",
            "message": "Email and password are required"
        }), 400

    conn = get_db()

    user = conn.execute(
        """
        SELECT id, name, email, role
        FROM users
        WHERE email = ? AND password = ?
        """,
        (email, password)
    ).fetchone()

    conn.close()

    if user:
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"]
            }
        })

    return jsonify({
        "status": "error",
        "message": "Invalid email or password"
    }), 401

@app.route("/api/complaints", methods=["POST"])
def create_complaint():
    data = request.get_json()

    user_id = data.get("user_id")
    description = data.get("description")
    location = data.get("location")

    if not user_id or not description or not location:
        return jsonify({
            "status": "error",
            "message": "user_id, description and location are required"
        }), 400

    conn = get_db()

    cursor = conn.execute(
        """
        INSERT INTO complaints (
            user_id,
            description,
            location
        )
        VALUES (?, ?, ?)
        """,
        (user_id, description, location)
    )

    conn.commit()

    complaint_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "status": "success",
        "message": "Complaint submitted successfully",
        "complaint_id": complaint_id
    }), 201

@app.route("/api/complaints", methods=["GET"])
def get_complaints():
    conn = get_db()

    complaints = conn.execute("""
        SELECT
            complaints.id,
            complaints.description,
            complaints.location,
            complaints.category,
            complaints.urgency,
            complaints.priority,
            complaints.credibility,
            complaints.is_duplicate,
            complaints.status,
            complaints.department,
            complaints.created_at,
            users.name AS citizen_name
        FROM complaints
        JOIN users ON complaints.user_id = users.id
        ORDER BY complaints.priority DESC, complaints.created_at DESC
    """).fetchall()

    conn.close()

    return jsonify([
        dict(complaint) for complaint in complaints
    ])

if __name__ == "__main__":
    init_db()
    app.run(debug=True)