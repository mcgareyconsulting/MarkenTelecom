from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import re
import os
from flask_cors import CORS
from dotenv import load_dotenv
import json
import uuid

from letter_generation import generate_pdfs
from database import db, init_db
from database.models import ViolationReport, Violation, ViolationImage
from utils.violation_codes import get_violation_titles_for_district

# Load environment variables from .env file
load_dotenv()


def create_app():
    """Application factory pattern"""
    app = Flask(__name__)

    # Configuration
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "your-secret-key-change-this"
    )

    # Database configuration
    if os.environ.get("FLASK_DEBUG", "0") == "1":
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///violations.db"
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # File upload configuration
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads/violation_images")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size

    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE
    app.config["ALLOWED_EXTENSIONS"] = ALLOWED_EXTENSIONS

    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Initialize database
    init_db(app)

    # Enable CORS
    CORS(app)

    return app


# Create app instance
app = create_app()

# Load and normalize muegge farms data
df = pd.read_excel("../datasets/MFMD_CL_250527.xlsx")
homeowner_records = df.to_dict(orient="records")


# Utility functions
def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename to prevent conflicts"""
    ext = (
        original_filename.rsplit(".", 1)[1].lower() if "." in original_filename else ""
    )
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    return unique_name


# Routes
@app.route("/api/address/autocomplete", methods=["GET"])
def autocomplete():
    """Address autocomplete endpoint"""
    query = request.args.get("q", "").lower()
    results = []

    for record in homeowner_records:
        if query in record["ServiceAddress"]:
            # Split city, state, zip
            city_state_zip = record.get("SvcCitySTZip", "")
            city, state, zip_code = "", "", ""

            try:
                # Example: "Bennett, CO 80010"
                parts = city_state_zip.split(",")
                if len(parts) == 2:
                    city = parts[0].strip()
                    state_zip = parts[1].strip().split(" ")
                    if len(state_zip) == 2:
                        state = state_zip[0]
                        zip_code = state_zip[1]
            except Exception as e:
                print(f"Error parsing city/state/zip: {city_state_zip} - {e}")

            results.append(
                {
                    "service_address": record["ServiceAddress"],
                    "city": city,
                    "state": state,
                    "zip": zip_code,
                }
            )

            if len(results) >= 10:
                break

    return jsonify(results)


@app.route("/api/violations_list_per_district", methods=["GET"])
def get_violation_list():
    """
    API endpoint to get violation titles for a given district.
    Usage: /api/violation_titles?district=waters_edge
    """
    district = request.args.get("district")
    if not district:
        return jsonify({"error": "Missing district parameter"}), 400

    try:
        titles = get_violation_titles_for_district(district)
        return jsonify({"titles": titles})
    except Exception as e:
        print(f"Error fetching violation titles: {e}")
        return jsonify({"error": "Failed to fetch violation titles"}), 500


@app.route("/api/violations", methods=["POST"])
def create_violation_report():
    """Create a new violation report with images"""
    try:
        # Ensure form data is present
        if not request.form or "data" not in request.form:
            return jsonify({"error": "Missing form data"}), 400

        data = json.loads(request.form["data"])
        print("Received data:", data)

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
        print(f"Error in create_violation_report: {e}")
        return jsonify({"error": "Failed to create violation report"}), 500


@app.route("/api/images/<filename>")
def serve_image(filename: str):
    """Serve uploaded images"""
    try:
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
    except Exception as e:
        return jsonify({"error": "Image not found"}), 404


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
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
