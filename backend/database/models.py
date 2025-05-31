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
