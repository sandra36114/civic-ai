from flask import Flask, jsonify, request, render_template
from database import init_db, get_db
from ai.predictor import analyze_complaint

app = Flask(__name__)

app.secret_key = "civicai-secret-key"


@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/complaint")
def complaint_page():
    return render_template("complaint.html")

@app.route("/admin")
def admin_page():
    return render_template("admin.html")

@app.route("/complaint-result/<int:complaint_id>")
def complaint_result(complaint_id):
    conn = get_db()

    complaint = conn.execute(
        """
        SELECT
            id,
            description,
            location,
            category,
            urgency,
            priority,
            credibility,
            is_duplicate,
            status,
            department,
            created_at
        FROM complaints
        WHERE id = ?
        """,
        (complaint_id,)
    ).fetchone()

    conn.close()

    if not complaint:
        return "Complaint not found", 404

    return render_template(
        "complaint_result.html",
        complaint=dict(complaint)
    )

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
    has_evidence = data.get("has_evidence", False)

    if not user_id or not description or not location:
        return jsonify({
            "status": "error",
            "message": "user_id, description and location are required"
        }), 400

    conn = get_db()

    # Get previous complaints for duplicate detection
    previous_rows = conn.execute(
        "SELECT description FROM complaints"
    ).fetchall()

    previous_complaints = [
        row["description"] for row in previous_rows
    ]

    # Run AI analysis
    analysis = analyze_complaint(
        description=description,
        location=location,
        has_evidence=has_evidence,
        previous_complaints=previous_complaints
    )

    # Insert complaint with AI results
    cursor = conn.execute(
        """
        INSERT INTO complaints (
            user_id,
            description,
            location,
            category,
            urgency,
            priority,
            credibility,
            is_duplicate,
            status,
            department
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            description,
            location,
            analysis["category"],
            analysis["urgency"],
            analysis["priority"],
            analysis["credibility"],
            int(analysis["duplicate"]),
            "Needs Review",
            analysis["category"] + " Department"
        )
    )

    conn.commit()

    complaint_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "status": "success",
        "message": "Complaint submitted and analyzed successfully",
        "complaint_id": complaint_id,
        "ai_analysis": analysis
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

@app.route("/api/complaints/<int:complaint_id>/status", methods=["PUT"])
def update_complaint_status(complaint_id):
    data = request.get_json()

    status = data.get("status")
    department = data.get("department")

    allowed_statuses = [
        "Submitted",
        "Needs Review",
        "Verified",
        "Assigned",
        "In Progress",
        "Resolved"
    ]

    if status not in allowed_statuses:
        return jsonify({
            "status": "error",
            "message": "Invalid complaint status"
        }), 400

    conn = get_db()

    complaint = conn.execute(
        "SELECT id FROM complaints WHERE id = ?",
        (complaint_id,)
    ).fetchone()

    if not complaint:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Complaint not found"
        }), 404

    conn.execute(
        """
        UPDATE complaints
        SET status = ?,
            department = COALESCE(?, department)
        WHERE id = ?
        """,
        (status, department, complaint_id)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Complaint updated successfully"
    })

@app.route("/api/users/<int:user_id>/complaints", methods=["GET"])
def get_user_complaints(user_id):
    conn = get_db()

    complaints = conn.execute("""
        SELECT
            id,
            description,
            location,
            category,
            urgency,
            priority,
            credibility,
            is_duplicate,
            status,
            department,
            created_at
        FROM complaints
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()

    conn.close()

    return jsonify([
        dict(complaint) for complaint in complaints
    ])

@app.route("/api/admin/complaints", methods=["GET"])
def get_admin_complaints():
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
            users.name AS citizen_name,
            users.email AS citizen_email
        FROM complaints
        JOIN users ON complaints.user_id = users.id
        ORDER BY complaints.priority DESC, complaints.created_at DESC
    """).fetchall()

    conn.close()

    return jsonify([
        dict(complaint) for complaint in complaints
    ])

@app.route("/api/admin/stats", methods=["GET"])
def get_admin_stats():
    conn = get_db()

    total_complaints = conn.execute(
        "SELECT COUNT(*) FROM complaints"
    ).fetchone()[0]

    critical_complaints = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE urgency = 'Critical'"
    ).fetchone()[0]

    high_priority = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE priority >= 70"
    ).fetchone()[0]

    pending_review = conn.execute(
        """
        SELECT COUNT(*)
        FROM complaints
        WHERE status = 'Needs Review'
        """
    ).fetchone()[0]

    resolved_complaints = conn.execute(
        """
        SELECT COUNT(*)
        FROM complaints
        WHERE status = 'Resolved'
        """
    ).fetchone()[0]

    conn.close()

    return jsonify({
        "status": "success",
        "stats": {
            "total_complaints": total_complaints,
            "critical_complaints": critical_complaints,
            "high_priority": high_priority,
            "pending_review": pending_review,
            "resolved_complaints": resolved_complaints
        }
    })
@app.route("/submit-complaint", methods=["POST"])
def submit_complaint():

    user_id = request.form.get("user_id")
    description = request.form.get("description")
    location = request.form.get("location")
    has_evidence = request.form.get("has_evidence") == "true"

    if not user_id or not description or not location:
        return "Missing required information", 400

    conn = get_db()

    previous_rows = conn.execute(
        "SELECT description FROM complaints"
    ).fetchall()

    previous_complaints = [
        row["description"] for row in previous_rows
    ]

    analysis = analyze_complaint(
        description=description,
        location=location,
        has_evidence=has_evidence,
        previous_complaints=previous_complaints
    )

    conn.execute("""
        INSERT INTO complaints (
            user_id,
            description,
            location,
            category,
            urgency,
            priority,
            credibility,
            is_duplicate,
            status,
            department
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        int(user_id),
        description,
        location,
        analysis["category"],
        analysis["urgency"],
        analysis["priority"],
        analysis["credibility"],
        int(analysis["duplicate"]),
        "Needs Review",
        analysis["category"] + " Department"
    ))

    conn.commit()
    conn.close()

    return f"""
    <html>
    <head>
        <title>CivicAI - Complaint Submitted</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f3f6fa;
                text-align: center;
                padding-top: 100px;
            }}

            .card {{
                background: white;
                width: 500px;
                margin: auto;
                padding: 40px;
                border-radius: 18px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }}

            h1 {{
                color: #1565c0;
            }}

            .result {{
                text-align: left;
                margin-top: 25px;
                font-size: 18px;
                line-height: 1.8;
            }}

            a {{
                display: inline-block;
                margin-top: 25px;
                padding: 12px 25px;
                background: #1565c0;
                color: white;
                text-decoration: none;
                border-radius: 8px;
            }}
        </style>
    </head>

    <body>

        <div class="card">

            <h1>Complaint Submitted! ✅</h1>

            <p>CivicAI has analyzed your complaint.</p>

            <div class="result">

                <b>Category:</b>
                {analysis["category"]}

                <br>

                <b>Urgency:</b>
                {analysis["urgency"]}

                <br>

                <b>Priority:</b>
                {analysis["priority"]}/100

                <br>

                <b>Credibility:</b>
                {analysis["credibility"]}/100

                <br>

                <b>Duplicate:</b>
                {"Yes" if analysis["duplicate"] else "No"}

            </div>

            <a href="/dashboard">
                Go to Dashboard
            </a>

        </div>

    </body>
    </html>
    """

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
