from flask import Flask, request, jsonify
import pandas as pd
import re
import os
from flask_cors import CORS
from letter_generation import generate_pdfs

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variable to store the data
address_data = None


def load_data(excel_file="../saddler_ridge.xlsx"):
    """Load data from Excel file into memory"""
    global address_data
    try:
        # Check if file exists
        if not os.path.exists(excel_file):
            print(f"Error: File {excel_file} not found.")
            return False

        # Load the Excel file
        df = pd.read_excel(excel_file)

        # Check if required columns exist
        required_columns = ["ServiceAddress", "Account Number", "Account Name"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            print(f"Error: Missing required columns: {', '.join(missing_columns)}")
            return False

        # Filter out rows with missing ServiceAddress
        df = df.dropna(subset=["ServiceAddress"])

        # Store the data in memory
        address_data = df
        print(f"Successfully loaded {len(df)} addresses from {excel_file}")
        return True
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return False


@app.route("/api/address/autocomplete", methods=["GET"])
def autocomplete():
    """API endpoint for address autocomplete"""
    # Check if data is loaded
    if address_data is None:
        success = load_data()
        if not success:
            return jsonify({"error": "Failed to load address data"}), 500

    # Get query parameters
    query = request.args.get("q", "")
    limit = request.args.get("limit", 5, type=int)

    # Validate query
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400

    try:
        # Case-insensitive search for partial matches
        pattern = re.compile(re.escape(query), re.IGNORECASE)

        # Filter the dataframe
        matches = address_data[
            address_data["ServiceAddress"].str.contains(pattern, na=False)
        ]

        # Limit the number of results
        matches = matches.head(limit)

        # Format the results
        suggestions = []
        for _, row in matches.iterrows():
            suggestion = {
                "address": row["ServiceAddress"],
                "account_number": row["Account Number"],
                "account_name": row["Account Name"],
            }
            suggestions.append(suggestion)

        return jsonify({"suggestions": suggestions})

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


def generate_violation_notices(district, date):
    """
    Generate violation noticies for addresses in district and on a specific date.
    """

    # Query database for violations: district and date

    # Build data package for PDF generation
    generate_pdfs()


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    load_data()
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
