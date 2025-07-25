import re
from database.models import District, Account, ViolationReport
from pdf_generator.generate_pdf import ViolationNoticePDF
from utils.violation_codes import violations
from datetime import datetime, date
from database import db


class AddressNormalizer:
    """Handles address normalization and matching logic."""

    SUFFIX_MAP = {
        " street": " st",
        " avenue": " ave",
        " boulevard": " blvd",
        " drive": " dr",
        " road": " rd",
        " lane": " ln",
        " court": " ct",
        " place": " pl",
        " trail": " trl",
        " parkway": " pkwy",
        " circle": " cir",
        " terrace": " ter",
        " way": " wy",  # sometimes way or sometimes wy
    }

    @classmethod
    def normalize(cls, addr):
        """Normalize address for consistent matching."""
        if not addr:
            return ""

        addr = addr.strip().lower()
        # Remove punctuation
        addr = re.sub(r"[.,]", "", addr)
        # Collapse multiple spaces
        addr = re.sub(r"\s+", " ", addr)
        # Remove trailing whitespace (again, in case replacements add it)
        addr = addr.rstrip()

        # Replace street suffixes
        for long_form, short_form in cls.SUFFIX_MAP.items():
            if addr.endswith(long_form):
                addr = addr[: -len(long_form)] + short_form
            addr = addr.replace(long_form + " ", short_form + " ")
        # Final strip to ensure no trailing whitespace
        return addr.strip()


class ViolationDataCollector:
    """Collects and processes violation data for PDF generation."""

    def __init__(self, district_name):
        self.district_name = district_name
        self.district = self._get_district()

    def _get_district(self):
        """Get district from database."""
        district = District.query.filter_by(name=self.district_name).first()
        if not district:
            raise ValueError(f"District '{self.district_name}' not found in database")
        return district

    def _get_accounts_lookup(self):
        """Create normalized address lookup for accounts."""
        accounts = Account.query.filter_by(district_id=self.district.id).all()
        return {
            AddressNormalizer.normalize(account.service_address): account
            for account in accounts
        }

    def _get_violation_reports(self):
        """Get all violation reports for the district updated today."""
        dates = [date(2025, 7, 8), date(2025, 7, 9)]
        filters = []
        for target_date in dates:
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = datetime.combine(target_date, datetime.max.time())
            filters.append(
                (ViolationReport.updated_at >= start_dt)
                & (ViolationReport.updated_at <= end_dt)
            )
        return ViolationReport.query.filter(
            ViolationReport.district == self.district_name, (filters[0]) | (filters[1])
        ).all()

    def _get_district_regulations(self, district_name, violation_type):
        """Fetch district regulations for a specific violation type."""
        # if violation is other then do not return regulation info
        if violation_type == "other":
            return {
                "violation_name": "Other",
                "title": "Other Violation",
                "description": "No specific regulation available for this violation type.",
            }
        try:
            return {
                "violation_name": violation_type,
                "title": violations[district_name][violation_type]["title"],
                "description": violations[district_name][violation_type]["description"],
            }
        except KeyError:
            # If the violation type or district is not found, skip this violation
            return None

    def _create_pdf_data_package(self, account, report, violation):
        """Create a complete data package for PDF generation."""
        violation_images = [
            {
                "filename": image.filename,
                "file_path": image.file_path,
                "original_filename": image.original_filename,
            }
            for image in violation.images
        ]

        regulation_info = self._get_district_regulations(
            self.district_name, violation.violation_type
        )

        return {
            # District information
            "district_name": self.district.name,
            "district_label": self.district.label,
            "district_code": self.district.code,
            # Homeowner information
            "homeowner_name": account.account_name,
            "account_number": account.account_number,
            "lot_number": account.lot_number,
            "homeowner_email": account.email,
            # Property addresses
            "property_address": report.address_line1,
            "property_address_line2": report.address_line2,
            "property_city": report.city,
            "property_state": report.state,
            "property_zip": report.zip_code,
            # Mailing addresses
            "mailing_address": account.mail_address,
            "mailing_city_st_zip": account.mail_city_st_zip,
            "service_address": account.service_address,
            "service_city_st_zip": account.service_city_st_zip,
            # Violation information
            "violation_id": violation.id,
            "violation_type": violation.violation_type,
            "violation_notes": violation.notes,
            "violation_date": violation.created_at.strftime("%Y-%m-%d"),
            "violation_images": violation_images,
            # Regulation information
            "regulation": regulation_info,
            # Report information
            "report_id": report.id,
            "report_status": report.status,
            "report_created_at": report.created_at.strftime("%Y-%m-%d"),
            "report_updated_at": report.updated_at.strftime("%Y-%m-%d"),
        }

    def collect_violation_data(self):
        """Main method to collect all violation data for PDF generation."""
        print(f"Collecting violation data for: {self.district_name}")

        account_lookup = self._get_accounts_lookup()
        violation_reports = self._get_violation_reports()

        # Dictionary to group violations by address
        address_violations = {}
        matches_found = 0
        processed_violations = (
            set()
        )  # Track processed violation IDs to prevent duplicates

        for report in violation_reports:
            normalized_address = AddressNormalizer.normalize(report.address_line1)
            account = account_lookup.get(normalized_address)

            print(f"Checking: {report.address_line1} -> {normalized_address}")

            if account:
                matches_found += 1
                address_key = report.address_line1

                # Process each violation in the report
                for violation in report.violations:
                    # Skip if violation type is not in the district regulations
                    if (
                        violation.violation_type == "other"
                        or violation.violation_type == "bball_hoop"
                    ):
                        print(
                            f"Skipping 'other' / 'bball_hoop' violation for: {report.address_line1}"
                        )
                        continue

                    # Skip if we've already processed this violation ID
                    if violation.id in processed_violations:
                        print(
                            f"Skipping duplicate violation ID {violation.id} for: {report.address_line1}"
                        )
                        continue

                    processed_violations.add(violation.id)

                    pdf_data = self._create_pdf_data_package(account, report, violation)

                    # Add to address_violations dictionary
                    if address_key not in address_violations:
                        address_violations[address_key] = []

                    address_violations[address_key].append(pdf_data)
                    print(f"Added: {account.account_name} - {violation.violation_type}")
                    if violation.notes:
                        print(f"Notes: {violation.notes}")
            else:
                print(f"No account match for: {report.address_line1}")

        # Convert the dictionary to a list of violation groups
        consolidated_data = []
        for address, violations_list in address_violations.items():
            consolidated_data.append(violations_list)

        print(f"Total address matches: {matches_found}")
        print(f"Total addresses with violations: {len(consolidated_data)}")
        total_violations = sum(len(violations) for violations in consolidated_data)
        print(f"Total violations to process: {total_violations}")

        return consolidated_data


class PDFGenerator:
    """Handles PDF generation from violation data."""

    @staticmethod
    def generate_consolidated_pdfs(consolidated_data_list):
        """Generate consolidated PDFs for all addresses with violations."""
        generated_count = 0

        for violations_list in consolidated_data_list:
            if not violations_list:
                continue

            # All violations in this list are for the same address
            address = violations_list[0].get("property_address", "unknown")

            try:
                generator = ViolationNoticePDF()
                pdf_path = generator.generate_consolidated_pdf(violations_list)
                print(f"Consolidated PDF generated for {address}: {pdf_path}")
                generated_count += 1
            except Exception as e:
                print(f"Error generating consolidated PDF for {address}: {e}")

        print(f"Successfully generated {generated_count} consolidated PDFs")
        return generated_count

    @staticmethod
    def generate_pdfs(data_list):
        """Generate individual PDFs for all violation data packages (legacy method)."""
        generated_count = 0

        for data_dict in data_list:
            # Validate required fields
            if not data_dict.get("violation_type") or not data_dict.get(
                "homeowner_name"
            ):
                print(f"Skipping invalid data package: missing required fields")
                continue

            # Ensure notice_date is properly formatted
            if "notice_date" in data_dict and hasattr(
                data_dict["notice_date"], "strftime"
            ):
                data_dict["notice_date"] = data_dict["notice_date"].strftime("%Y-%m-%d")
            elif not data_dict.get("notice_date"):
                data_dict["notice_date"] = "N/A"

            try:
                generator = ViolationNoticePDF()
                pdf_path = generator.generate_pdf(data_dict)
                print(f"PDF generated: {pdf_path}")
                generated_count += 1
            except Exception as e:
                print(
                    f"Error generating PDF for {data_dict.get('property_address', 'unknown')}: {e}"
                )

        print(f"Successfully generated {generated_count} PDFs")
        return generated_count


# Main functions for backward compatibility
def violation_match(district_name):
    """Legacy function - use ViolationDataCollector.collect_violation_data() instead."""
    collector = ViolationDataCollector(district_name)
    return collector.collect_violation_data()


def collect_violation_data_for_pdf(district_name):
    """Main function to collect violation data ready for PDF generation."""
    collector = ViolationDataCollector(district_name)
    return collector.collect_violation_data()


def generate_pdfs(data_list):
    """Generate PDFs from violation data list."""
    return PDFGenerator.generate_pdfs(data_list)


def generate_consolidated_pdfs(consolidated_data_list):
    """Generate consolidated PDFs from grouped violation data list."""
    return PDFGenerator.generate_consolidated_pdfs(consolidated_data_list)
