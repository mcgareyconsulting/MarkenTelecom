"""
Database models for the violation reporting system
"""

from database import db
from datetime import datetime
from typing import Dict, Any


class ViolationReport(db.Model):
    """Main violation report model"""

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
        """Convert model to dictionary"""
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

    def __repr__(self):
        return f"<ViolationReport {self.id}: {self.address_line1}, {self.city}>"


class Violation(db.Model):
    """Individual violation within a report"""

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
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "type": self.violation_type,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "images": [image.to_dict() for image in self.images],
        }

    def __repr__(self):
        return f"<Violation {self.id}: {self.violation_type}>"


class ViolationImage(db.Model):
    """Images associated with violations"""

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
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "uploaded_at": self.uploaded_at.isoformat(),
            "url": f"/api/images/{self.filename}",
        }

    def __repr__(self):
        return f"<ViolationImage {self.id}: {self.filename}>"


"""
Database models for customer account management system.
Flask-SQLAlchemy models for managing customer accounts across different districts.
"""


class District(db.Model):
    """
    Represents a district or development area.
    This model allows for grouping accounts by their district/development.
    """

    __tablename__ = "districts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(
        db.String(10), nullable=False, unique=True
    )  # E.g., "WEMD" or "HMMD"
    description = db.Column(db.Text, nullable=True)

    # Relationships
    accounts = db.relationship(
        "Account", backref="district", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "accounts": [account.to_dict() for account in self.accounts],
        }

    def __repr__(self):
        return f"<District(name='{self.name}', code='{self.code}')>"


class Account(db.Model):
    """
    Represents a customer account.
    Contains all account information including service and mailing addresses.
    """

    __tablename__ = "accounts"

    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(
        db.String(20), nullable=False, unique=True
    )  # Format: "1440001-001"
    account_name = db.Column(db.String(100), nullable=False)
    lot_number = db.Column(
        db.String(50), nullable=False
    )  # Varied formats: "F02 Lot 1" or "H-M 1 B:01 L:01"
    move_in_date = db.Column(db.DateTime, nullable=True)
    address_type = db.Column(db.String(20), nullable=True)  # E.g., "Owner"

    # Service address fields
    service_address = db.Column(db.String(100), nullable=True)
    service_city_st_zip = db.Column(db.String(100), nullable=True)

    # Mailing address fields
    mail_address = db.Column(db.String(100), nullable=True)
    mail_city_st_zip = db.Column(db.String(100), nullable=True)

    # Contact information
    email = db.Column(db.String(100), nullable=True)
    ebill_username = db.Column(db.String(100), nullable=True)

    # Foreign keys
    district_id = db.Column(db.Integer, db.ForeignKey("districts.id"), nullable=False)

    # Relationships
    history = db.relationship(
        "AccountHistory", backref="account", lazy=True, cascade="all, delete-orphan"
    )
    contact_preferences = db.relationship(
        "ContactPreference", backref="account", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "account_number": self.account_number,
            "account_name": self.account_name,
            "lot_number": self.lot_number,
            "move_in_date": (
                self.move_in_date.isoformat() if self.move_in_date else None
            ),
            "address_type": self.address_type,
            "service_address": {
                "address": self.service_address,
                "city_st_zip": self.service_city_st_zip,
            },
            "mail_address": {
                "address": self.mail_address,
                "city_st_zip": self.mail_city_st_zip,
            },
            "email": self.email,
            "ebill_username": self.ebill_username,
            "district_id": self.district_id,
        }

    def __repr__(self):
        return f"<Account(account_number='{self.account_number}', account_name='{self.account_name}')>"


class AccountHistory(db.Model):
    """
    Tracks historical changes to accounts.
    This model allows for maintaining a history of account changes over time.
    """

    __tablename__ = "account_history"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=False)
    change_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    field_changed = db.Column(db.String(50), nullable=False)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    changed_by = db.Column(db.String(100), nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "account_id": self.account_id,
            "change_date": self.change_date.isoformat(),
            "field_changed": self.field_changed,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changed_by": self.changed_by,
        }

    def __repr__(self):
        return f"<AccountHistory(account_id={self.account_id}, field='{self.field_changed}')>"


class ContactPreference(db.Model):
    """
    Stores customer contact preferences.
    This model allows for tracking how customers prefer to be contacted.
    """

    __tablename__ = "contact_preferences"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=False)
    email_notifications = db.Column(db.Boolean, default=False)
    sms_notifications = db.Column(db.Boolean, default=False)
    mail_notifications = db.Column(db.Boolean, default=True)
    phone_number = db.Column(db.String(20), nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "account_id": self.account_id,
            "email_notifications": self.email_notifications,
            "sms_notifications": self.sms_notifications,
            "mail_notifications": self.mail_notifications,
            "phone_number": self.phone_number,
        }

    def __repr__(self):
        return f"<ContactPreference(account_id={self.account_id})>"


# Helper function to import data from Excel to database
def import_excel_to_db(excel_path, district_code, district_name=None):
    """
    Import data from Excel file to database.

    Args:
        excel_path: Path to Excel file
        district_code: District code (e.g., "WEMD" or "HMMD")
        district_name: Name of the district (will prompt if not provided)
    """
    import pandas as pd

    print(f"Starting import from: {excel_path}")
    print(f"Using district code: {district_code}")

    # Check if district exists, create if not
    district = District.query.filter_by(code=district_code).first()
    if not district:
        print(f"District '{district_code}' not found in database.")
        # Prompt for district name if not provided
        if district_name is None:
            district_name = input(f"Enter name for district '{district_code}': ")

        print(f"Creating new district: {district_name} ({district_code})")
        district = District(name=district_name, code=district_code)
        db.session.add(district)
        db.session.commit()
    else:
        print(f"Found district: {district.name} ({district.code})")

    # Read Excel file
    print("Reading Excel file...")
    df = pd.read_excel(excel_path)
    print(f"Loaded {len(df)} rows from Excel.")

    # Import accounts
    added = 0
    for idx, row in df.iterrows():
        account = Account(
            account_number=clean_value(row["Account Number"]),
            account_name=clean_value(row["Account Name"]),
            lot_number=clean_value(row["Lot Number"]),
            move_in_date=clean_value(row["Move In Date"]),
            address_type=clean_value(row["Address Type"]),
            service_address=clean_value(row["ServiceAddress"]),
            service_city_st_zip=clean_value(row["SvcCitySTZip"]),
            mail_address=clean_value(row["MailAddress"]),
            mail_city_st_zip=clean_value(row["MailCitySTZip"]),
            email=clean_value(row["Email"]),
            ebill_username=clean_value(row["EBill Username"]),
            district_id=district.id,
        )
        db.session.add(account)
        added += 1
        if added % 100 == 0:
            print(f"Processed {added} accounts...")

    db.session.commit()
    print(
        f"Import complete. {added} accounts added to district '{district.name}' ({district.code})."
    )


def clean_value(val):
    """
    Pandas to SQLAlchemy conversion helper function.
    """
    import math

    if val is None:
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    return val
