from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import re
import os
from flask_cors import CORS
from dotenv import load_dotenv
import json
import uuid
from datetime import datetime
from letter_generation import (
    ViolationDataCollector,
    PDFGenerator,
)
from pdf_generator.board_report import generate_board_report

# from letter_generation import generate_pdfs
from database import db, init_db
from database.models import (
    ViolationReport,
    Violation,
    ViolationImage,
    District,
    Account,
    AccountHistory,
    ContactPreference,
    import_excel_to_db,
)

# sqlalchemy import
from sqlalchemy import or_

# cloudinary import
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

# from utils.violation_codes import get_violation_titles_for_district

# Load environment variables from .env file
load_dotenv()

# Configuration
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
    secure=True,
)


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

# load dataset into db
with app.app_context():
    try:
        import_excel_to_db(
            excel_path="../datasets/SRMD_CL_250516.xlsx",
            district_code="SRMD",
            district_name="saddler_ridge",
            district_label="Saddler Ridge",
        )
        print("✅ Dataset imported successfully!")
    except Exception as e:
        print(f"❌ Error importing dataset: {e}")


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


@app.route("/api/district/<string:district_code>/accounts", methods=["GET"])
def get_district_accounts(district_code: str):
    """
    Get all accounts for a specific district by district code.
    Returns simplified account data optimized for autocomplete functionality.

    Args:
        district_code: The district code (e.g., 'ventana', 'winsome', 'mountain_sky')

    Query Parameters:
        limit: Maximum number of accounts to return (default: no limit)
        active_only: If true, only return accounts with service addresses (default: true)

    Returns:
        JSON array of account objects with service address info
    """
    try:
        # Get query parameters
        limit = request.args.get("limit", type=int)
        active_only = request.args.get("active_only", default="true").lower() == "true"

        # Map frontend district codes to database district codes/names
        # You may need to adjust this mapping based on your actual data
        district_code_mapping = {
            "ventana": ["VENTANA", "VMD"],
            "winsome": ["WINSOME", "WMD"],
            "waters_edge": ["WATERS_EDGE", "WEMD"],
            "highlands_mead": ["HIGHLANDS_MEAD", "HMMD"],
            "muegge_farms": ["MUEGGE_FARMS", "MFMD"],
            "mountain_sky": ["MOUNTAIN_SKY", "MSMD"],
            "littleton_village": ["LITTLETON_VILLAGE", "LVMD"],
            "red_barn": ["RED_BARN", "RBMD"],
        }

        # Get the possible district codes/names for this district
        possible_codes = district_code_mapping.get(
            district_code.lower(), [district_code.upper()]
        )

        # Find the district(s) in the database
        districts = District.query.filter(
            or_(
                District.code.in_(possible_codes),
                District.name.in_(possible_codes),
                District.label.in_(possible_codes),
            )
        ).all()

        if not districts:
            return (
                jsonify(
                    {
                        "error": f"District not found: {district_code}",
                        "available_districts": [d.code for d in District.query.all()],
                    }
                ),
                404,
            )

        # Get district IDs
        district_ids = [d.id for d in districts]

        # Build the query for accounts
        query = Account.query.filter(Account.district_id.in_(district_ids))

        # Filter for active accounts only (those with service addresses)
        if active_only:
            query = query.filter(Account.service_address.isnot(None))
            query = query.filter(Account.service_address != "")

        # Apply limit if specified
        if limit:
            query = query.limit(limit)

        # Execute query
        accounts = query.all()

        # Format the response for autocomplete
        formatted_accounts = []
        for account in accounts:
            # Parse city, state, zip from service_city_st_zip
            city, state, zip_code = parse_city_state_zip(account.service_city_st_zip)

            account_data = {
                "id": account.id,
                "account_number": account.account_number,
                "account_name": account.account_name,
                "service_address": account.service_address,
                "city": city,
                "state": state,
                "zip": zip_code,
                "district": district_code,  # Use the requested district code
                "lot_number": account.lot_number,
            }
            formatted_accounts.append(account_data)

        # Sort by service address for better UX
        formatted_accounts.sort(key=lambda x: x["service_address"] or "")

        return jsonify(formatted_accounts)

    except Exception as e:
        print(f"Error fetching district accounts: {str(e)}")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


def parse_city_state_zip(city_st_zip: str) -> tuple[str, str, str]:
    """
    Parse city, state, and zip from a combined string.

    Expected formats:
    - "Colorado Springs, CO 80908"
    - "Fountain, CO 80817"
    - "Fort Lupton, CO 80621"

    Args:
        city_st_zip: Combined city, state, zip string

    Returns:
        Tuple of (city, state, zip)
    """
    if not city_st_zip:
        return "", "", ""

    try:
        # Pattern to match "City, ST ZIP" format
        pattern = r"^(.+?),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$"
        match = re.match(pattern, city_st_zip.strip())

        if match:
            city = match.group(1).strip()
            state = match.group(2).strip()
            zip_code = match.group(3).strip()
            return city, state, zip_code
        else:
            # Fallback: try to split by comma and space
            parts = city_st_zip.split(",")
            if len(parts) >= 2:
                city = parts[0].strip()
                state_zip = parts[1].strip().split()
                if len(state_zip) >= 2:
                    state = state_zip[0].strip()
                    zip_code = state_zip[1].strip()
                    return city, state, zip_code
                elif len(state_zip) == 1:
                    # Could be just state or just zip
                    if state_zip[0].isdigit():
                        return city, "", state_zip[0]
                    else:
                        return city, state_zip[0], ""

            # If all else fails, return the original string as city
            return city_st_zip, "", ""

    except Exception as e:
        print(f"Error parsing city_st_zip '{city_st_zip}': {str(e)}")
        return city_st_zip or "", "", ""


# @app.route("/api/violations_list_per_district", methods=["GET"])
# def get_violation_list():
#     """
#     API endpoint to get violation titles for a given district.
#     Usage: /api/violation_titles?district=waters_edge
#     """
#     district = request.args.get("district")
#     if not district:
#         return jsonify({"error": "Missing district parameter"}), 400

#     try:
#         titles = get_violation_titles_for_district(district)
#         return jsonify({"titles": titles})
#     except Exception as e:
#         print(f"Error fetching violation titles: {e}")
#         return jsonify({"error": "Failed to fetch violation titles"}), 500


@app.route("/api/violations", methods=["POST"])
def create_violation_report():
    """Create a new violation report with images"""

    # temporary backdate for Muegge Farms data
    backdate = datetime(2025, 5, 30, 20, 58, 55, 211029)  # 2025-05-30 20:58:55.211029

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
            # created_at=backdate,  # Use backdated timestamp
        )

        db.session.add(report)
        db.session.flush()  # Get the report ID

        # Process violations
        for i, violation_data in enumerate(violations_data):
            violation = Violation(
                report_id=report.id,
                violation_type=violation_data.get("type", ""),
                notes=violation_data.get("notes", ""),
                # created_at=backdate,  # Use backdated timestamp
            )
            db.session.add(violation)
            db.session.flush()  # Get the violation ID

            # Handle image upload for this violation
            image_key = f"violation_{i}_image"
            if image_key in request.files:
                file = request.files[image_key]
                if file and file.filename and allowed_file(file.filename):
                    try:
                        # Upload to Cloudinary
                        upload_result = cloudinary.uploader.upload(
                            file,
                            folder="violations",
                            use_filename=True,
                            unique_filename=True,
                        )

                        # Extract necessary metadata
                        public_id = upload_result["public_id"]
                        secure_url = upload_result["secure_url"]
                        original_filename = file.filename

                        # Save to your DB
                        violation_image = ViolationImage(
                            violation_id=violation.id,
                            filename=public_id,  # or upload_result["original_filename"]
                            original_filename=original_filename,
                            file_path=secure_url,  # this now holds the Cloudinary URL
                            file_size=upload_result.get("bytes", 0),
                            mime_type=upload_result.get("resource_type", "image"),
                            # uploaded_at=backdate, # removing because we do not need to backdate
                        )
                        db.session.add(violation_image)

                    except Exception as upload_err:
                        print(f"Cloudinary upload failed: {upload_err}")

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

    # run join on district and address
    # with app.app_context():
    #     # New object-oriented approach (recommended)
    #     collector = ViolationDataCollector("littleton_village")
    #     consolidated_data = collector.collect_violation_data()
    #     violations = [v for group in consolidated_data for v in group]
    #     print(
    #         f"Collected {len(consolidated_data)} violation records for PDF generation."
    #     )
    #     PDFGenerator.generate_consolidated_pdfs(consolidated_data)
    # board report
    # generate_board_report(
    #     output_path="board_report.pdf",
    #     district_name="Highlands Mead",
    #     violations=violations,
    #     date=datetime.now().strftime("%B %d, %Y"),
    # )
    app.run(debug=debug_mode, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
