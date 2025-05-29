from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import re
import os
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from typing import Dict, Any
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# init app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "your-secret-key-change-this")

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///violations.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# File upload configuration
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads/violation_images")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)
# Enable CORS for the Flask app
CORS(app)  # Enable CORS for all routes


###################
# Database Models #
###################
class ViolationReport(db.Model):
    __tablename__ = "violation_reports"

    id = db.Column(db.Integer, primary_key=True)
    # Address fields
    address_line1 = db.Column(db.String(255), nullable=False)
    address_line2 = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    district = db.Column(db.String(100), nullable=False)

    # Report metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    status = db.Column(
        db.String(50), nullable=False, default="pending"
    )  # pending, reviewed, resolved

    # Relationships
    violations = db.relationship(
        "Violation", backref="report", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "address": {
                "line1": self.address_line1,
                "line2": self.address_line2,
                "city": self.city,
                "state": self.state,
                "zip": self.zip_code,
                "district": self.district,
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status,
            "violations": [violation.to_dict() for violation in self.violations],
        }


class Violation(db.Model):
    __tablename__ = "violations"

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(
        db.Integer, db.ForeignKey("violation_reports.id"), nullable=False
    )
    violation_type = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    images = db.relationship(
        "ViolationImage", backref="violation", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.violation_type,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "images": [image.to_dict() for image in self.images],
        }


class ViolationImage(db.Model):
    __tablename__ = "violation_images"

    id = db.Column(db.Integer, primary_key=True)
    violation_id = db.Column(db.Integer, db.ForeignKey("violations.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "uploaded_at": self.uploaded_at.isoformat(),
            "url": f"/api/images/{self.filename}",
        }


#######################
# End Database Models #
#######################


# Utility functions
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename to prevent conflicts"""
    ext = (
        original_filename.rsplit(".", 1)[1].lower() if "." in original_filename else ""
    )
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    return unique_name


# # Global variable to store the data
# address_data = None


# def load_data(excel_file="../saddler_ridge.xlsx"):
#     """Load data from Excel file into memory"""
#     global address_data
#     try:
#         # Check if file exists
#         if not os.path.exists(excel_file):
#             print(f"Error: File {excel_file} not found.")
#             return False

#         # Load the Excel file
#         df = pd.read_excel(excel_file)

#         # Check if required columns exist
#         required_columns = ["ServiceAddress", "Account Number", "Account Name"]
#         missing_columns = [col for col in required_columns if col not in df.columns]

#         if missing_columns:
#             print(f"Error: Missing required columns: {', '.join(missing_columns)}")
#             return False

#         # Filter out rows with missing ServiceAddress
#         df = df.dropna(subset=["ServiceAddress"])

#         # Store the data in memory
#         address_data = df
#         print(f"Successfully loaded {len(df)} addresses from {excel_file}")
#         return True
#     except Exception as e:
#         print(f"Error loading data: {str(e)}")
#         return False


# api routes
@app.route("/api/violations", methods=["POST"])
def create_violation_report():
    """Create a new violation report with images"""
    try:
        # Ensure form data is present
        if not request.form or "data" not in request.form:
            return jsonify({"error": "Missing form data"}), 400

        import json

        data = json.loads(request.form["data"])

        # Validate required fields
        address = data.get("address", {})
        violations_data = data.get("violations", [])

        if (
            not address.get("line1")
            or not address.get("city")
            or not address.get("state")
            or not address.get("zip")
            or not address.get("district")
        ):
            return jsonify({"error": "Missing required address fields"}), 400

        if not violations_data:
            return jsonify({"error": "At least one violation is required"}), 400

        # Create violation report
        report = ViolationReport(
            address_line1=address["line1"],
            address_line2=address.get("line2", ""),
            city=address["city"],
            state=address["state"],
            zip_code=address["zip"],
            district=address["district"],
        )

        db.session.add(report)
        db.session.flush()  # Get the report ID

        # Process violations
        for i, violation_data in enumerate(violations_data):
            violation = Violation(
                report_id=report.id,
                violation_type=violation_data.get("type", ""),
                notes=violation_data.get("notes", ""),
            )
            db.session.add(violation)
            db.session.flush()  # Get the violation ID

            # Handle image upload for this violation
            image_key = f"violation_{i}_image"
            if image_key in request.files:
                file = request.files[image_key]
                if file and file.filename and allowed_file(file.filename):
                    # Generate unique filename
                    filename = generate_unique_filename(file.filename)
                    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

                    # Save file
                    file.save(filepath)

                    # Create image record
                    violation_image = ViolationImage(
                        violation_id=violation.id,
                        filename=filename,
                        original_filename=file.filename,
                        file_path=filepath,
                        file_size=os.path.getsize(filepath),
                        mime_type=file.mimetype or "application/octet-stream",
                    )
                    db.session.add(violation_image)

        # Commit all changes
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Violation report created successfully",
                    "report_id": report.id,
                    "report": report.to_dict(),
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        # Log the error for debugging
        print(f"Error in create_violation_report: {e}")
        return jsonify({"error": "Failed to create violation report"}), 500


# @app.route("/api/address/autocomplete", methods=["GET"])
# def autocomplete():
#     """API endpoint for address autocomplete"""
#     # Check if data is loaded
#     if address_data is None:
#         success = load_data()
#         if not success:
#             return jsonify({"error": "Failed to load address data"}), 500

#     # Get query parameters
#     query = request.args.get("q", "")
#     limit = request.args.get("limit", 5, type=int)

#     # Validate query
#     if not query:
#         return jsonify({"error": "Missing query parameter 'q'"}), 400

#     try:
#         # Case-insensitive search for partial matches
#         pattern = re.compile(re.escape(query), re.IGNORECASE)

#         # Filter the dataframe
#         matches = address_data[
#             address_data["ServiceAddress"].str.contains(pattern, na=False)
#         ]

#         # Limit the number of results
#         matches = matches.head(limit)

#         # Format the results
#         suggestions = []
#         for _, row in matches.iterrows():
#             suggestion = {
#                 "address": row["ServiceAddress"],
#                 "account_number": row["Account Number"],
#                 "account_name": row["Account Name"],
#             }
#             suggestions.append(suggestion)

#         return jsonify({"suggestions": suggestions})

#     except Exception as e:
#         print(f"Error processing request: {str(e)}")
#         return jsonify({"error": "Internal server error"}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok"})


# Error handlers
@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum size is 16MB."}), 413


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Only use debug mode if not in production
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"

    # Create tables
    with app.app_context():
        db.create_all()

    # Run the app (for development only; use Gunicorn or uWSGI in production)
    app.run(debug=debug_mode, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
