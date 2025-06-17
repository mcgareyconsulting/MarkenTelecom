from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib.units import inch
from datetime import datetime
import os
from PIL import Image as PILImage, ExifTags, ImageEnhance, ImageFilter
import io
import requests


class ViolationNoticePDF:
    def __init__(self, output_dir="pdf_generator/output"):
        """Initialize the PDF generator with output directory."""
        self.output_dir = output_dir

        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Set up styles
        self.styles = getSampleStyleSheet()
        self.styles.add(
            ParagraphStyle(
                name="DistrictName",
                fontName="Helvetica-Bold",
                fontSize=18,
                textColor=HexColor("#2a4d8f"),  # A nice blue
                spaceAfter=0.15 * inch,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="DistrictInfo",
                fontName="Helvetica",
                fontSize=10,
                leading=12,
                spaceAfter=0.1 * inch,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="NoticeTitle",
                fontName="Helvetica-Bold",
                fontSize=14,
                alignment=1,  # Center
                spaceAfter=0.2 * inch,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Date",
                fontName="Helvetica",
                fontSize=10,
                alignment=2,  # Right
                spaceAfter=0.1 * inch,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Recipient",
                fontName="Helvetica",
                fontSize=10,
                spaceAfter=0.1 * inch,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="PropertyInfo",
                fontName="Helvetica",
                fontSize=10,
                spaceAfter=0.05 * inch,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="ViolationInfo",
                fontName="Helvetica-Bold",
                fontSize=10,
                spaceAfter=0.1 * inch,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Content", fontName="Helvetica", fontSize=10, spaceAfter=0.1 * inch
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Closing",
                fontName="Helvetica",
                fontSize=10,
                spaceAfter=0.05 * inch,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Signature",
                fontName="Helvetica-Bold",
                fontSize=10,
                spaceAfter=0.2 * inch,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="ImageCaption",
                fontName="Helvetica-Bold",
                fontSize=10,
                alignment=1,  # Center
                spaceAfter=0.1 * inch,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="RegulationCode",
                fontName="Helvetica-Bold",
                fontSize=12,
                spaceAfter=0.05 * inch,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="RegulationTitle",
                fontName="Helvetica-Bold",
                fontSize=11,
                spaceAfter=0.05 * inch,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="RegulationText",
                fontName="Helvetica",
                fontSize=10,
                spaceAfter=0.2 * inch,
                leading=12,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="ViolationHeader",
                fontName="Helvetica-Bold",
                fontSize=12,
                spaceAfter=0.1 * inch,
            )
        )

    def _format_date(self, date_value):
        """
        Convert date formats to 'Month Dayth, Year' (e.g., May 20th, 2025).
        Handles datetime objects, pandas Timestamps, and strings in MM/DD/YYYY or YYYY-MM-DD format.
        """

        def day_with_suffix(day):
            # Returns day with ordinal suffix (e.g., 1st, 2nd, 3rd, 4th, etc.)
            if 11 <= day <= 13:
                return f"{day}th"
            last = day % 10
            if last == 1:
                return f"{day}st"
            elif last == 2:
                return f"{day}nd"
            elif last == 3:
                return f"{day}rd"
            else:
                return f"{day}th"

        # Handle pandas Timestamp or datetime
        if hasattr(date_value, "strftime"):
            day = int(date_value.strftime("%d"))
            return f"{date_value.strftime('%B')} {day_with_suffix(day)}, {date_value.strftime('%Y')}"

        # Handle string in MM/DD/YYYY or YYYY-MM-DD format
        if isinstance(date_value, str):
            for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
                try:
                    parsed = datetime.strptime(date_value, fmt)
                    day = parsed.day
                    return f"{parsed.strftime('%B')} {day_with_suffix(day)}, {parsed.strftime('%Y')}"
                except Exception:
                    continue
            return date_value  # fallback to original string

        # Fallback
        return str(date_value)

    def _fetch_and_prepare_image(
        self, image_url, max_width=600, max_height=900, quality=95, sharpen_factor=1.0
    ):
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            img_data = response.content

            pil_img = PILImage.open(io.BytesIO(img_data))
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")

            try:
                for orientation in ExifTags.TAGS:
                    if ExifTags.TAGS[orientation] == "Orientation":
                        break
                exif = pil_img._getexif()
                if exif is not None:
                    orientation_value = exif.get(orientation)
                    if orientation_value == 3:
                        pil_img = pil_img.rotate(180, expand=True)
                    elif orientation_value == 6:
                        pil_img = pil_img.rotate(270, expand=True)
                    elif orientation_value == 8:
                        pil_img = pil_img.rotate(90, expand=True)
            except Exception:
                pass

            width, height = pil_img.size
            ratio = min(max_width / width, max_height / height, 1)
            new_width = int(width * ratio)
            new_height = int(height * ratio)

            if width > new_width * 2 or height > new_height * 2:
                intermediate_img = pil_img.resize(
                    (int(new_width * 1.5), int(new_height * 1.5)), PILImage.LANCZOS
                )
                pil_img = intermediate_img.resize(
                    (new_width, new_height), PILImage.LANCZOS
                )
            else:
                pil_img = pil_img.resize((new_width, new_height), PILImage.LANCZOS)

            output_buffer = io.BytesIO()
            pil_img.save(output_buffer, format="PNG", optimize=True)
            output_buffer.seek(0)

            # Fixed display size (2"x3" = 144pt x 216pt)
            reportlab_img = Image(output_buffer, width=144, height=216)
            reportlab_img.hAlign = "CENTER"

            return reportlab_img
        except Exception as e:
            print(f"Error processing image: {e}")
            return None

    def _add_header_content(self, data, content):
        """Add the header content to the PDF (district info, recipient, etc.)"""
        # District name (large and blue)
        content.append(
            Paragraph(
                f"{data['district_label']} Metropolitan District",
                self.styles["DistrictName"],
            )
        )

        # District address block (standard style)
        district_address_block = """c/o Public Alliance LLC<br/>
                         7555 E. Hampden Ave., Suite 501<br/>
                         Denver, CO 80231<br/>
                         (720) 213-6621"""
        content.append(Paragraph(district_address_block, self.styles["DistrictInfo"]))

        # Notice title
        content.append(Paragraph("Courtesy Notice", self.styles["NoticeTitle"]))

        # Format the date to ensure it's a string
        formatted_date = self._format_date(data["violation_date"])
        content.append(Paragraph(formatted_date, self.styles["Date"]))

        # Recipient information
        recipient_info = f"""{data['homeowner_name']}<br/>
                          {data['mailing_address']}<br/>
                          {data['mailing_city_st_zip']}"""

        # Add second address line if available
        if "mailing_address_line2" in data and data["mailing_address_line2"]:
            recipient_info += f"<br/>{data['mailing_address_line2']}"

        content.append(Paragraph(recipient_info, self.styles["Recipient"]))

        # Email if available
        if "homeowner_email" in data and data["homeowner_email"]:
            print(
                f"Homeowner {data['homeowner_name']} has email: {data['homeowner_email']}"
            )
            content.append(
                Paragraph(
                    f"Sent Via Email: {data['homeowner_email']}",
                    self.styles["PropertyInfo"],
                )
            )
        else:
            print(f"Homeowner {data['homeowner_name']} does not have an email address.")

        # Property information
        content.append(
            Paragraph(
                f"Property: {data['property_address']}", self.styles["PropertyInfo"]
            )
        )

        # Salutation if available
        if "homeowner_salutation" in data and data["homeowner_salutation"]:
            content.append(
                Paragraph(
                    f"Dear: {data['homeowner_salutation']},", self.styles["Content"]
                )
            )

        # Letter content
        letter_content = f"""One of the primary responsibilities of {data['district_label']} Metropolitan District ("the District") is to protect the aesthetic appeal and property values
        of the neighborhood. To accomplish this, certain Covenants and Design Guidelines have
        been established by which homeowners and residents must abide. During a recent
        inspection the following concerns were noted regarding your property and the District is asking for your
        help in achieving compliance."""
        content.append(Paragraph(letter_content, self.styles["Content"]))

        return content

    def _add_violation_content(self, violation_data, content, violation_number=None):
        """Add a single violation's content to the PDF"""

        # Collect regulation information
        regulation = violation_data["regulation"]

        # Add violation header with number if provided
        if violation_number is not None:
            content.append(
                Paragraph(
                    f"Violation {violation_number}: {regulation['title']}",
                    self.styles["ViolationHeader"],
                )
            )
        else:
            content.append(
                Paragraph(
                    f"Violation: {regulation['title']}",
                    self.styles["ViolationHeader"],
                )
            )

        # Dynamically insert newlines before each bullet point for better formatting
        formatted_description = regulation["description"].replace("•", "<br/>•")

        content.append(Paragraph(formatted_description, self.styles["RegulationText"]))

        # Add violation image if available
        if (
            violation_data["violation_images"]
            and len(violation_data["violation_images"]) > 0
        ):
            violation_image = violation_data["violation_images"][0]
            img = self._fetch_and_prepare_image(violation_image["file_path"])
            if img:
                content.append(img)
                content.append(
                    Paragraph("Violation Image", self.styles["ImageCaption"])
                )
            else:
                content.append(
                    Paragraph("Image not available", self.styles["ImageCaption"])
                )

        return content

    def _add_footer_content(self, data, content):
        """Add the footer content to the PDF (closing, signature, etc.)"""
        content.append(
            Paragraph(
                """We ask that you remedy these matters within the next 30 days from the date of this letter.
        Failure to do so may result in potential fines per the governing documents.""",
                self.styles["Content"],
            )
        )

        content.append(
            Paragraph(
                """If you have already resolved the above matters, we thank you for your prompt attention and
        appreciate your help keeping the neighborhood looking its best.""",
                self.styles["Content"],
            )
        )

        # Closing
        content.append(Paragraph("Sincerely,", self.styles["Closing"]))
        content.append(
            Paragraph(
                f"{data['district_label']} Metropolitan District",
                self.styles["Signature"],
            )
        )

        return content

    def generate_consolidated_pdf(self, violations_data):
        """
        Generate a consolidated PDF notice for multiple violations at the same address.

        Args:
            violations_data (list): List of violation data dictionaries for the same address

        Returns:
            str: Path to the generated PDF file
        """
        if not violations_data or len(violations_data) == 0:
            raise ValueError("No violation data provided")

        # Use the first violation's data for common information
        first_data = violations_data[0]

        # Generate a filename based on property address and date
        safe_address = (
            first_data["property_address"]
            .replace(" ", "_")
            .replace(",", "")
            .replace(".", "")
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_address}_{timestamp}.pdf"
        output_path = os.path.join(self.output_dir, filename)

        # Create the PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        # Build the content
        content = []

        # Add header content (only once)
        content = self._add_header_content(first_data, content)

        # Create a set to track unique violations by ID to prevent duplicates
        processed_violations = set()

        # Add each violation with a page break between them
        for i, violation_data in enumerate(violations_data):
            # Skip duplicates by checking violation ID
            violation_id = violation_data.get("violation_id")
            if violation_id in processed_violations:
                continue

            processed_violations.add(violation_id)

            # Add page break before violations after the first one
            if i > 0:
                content.append(PageBreak())

            # Add the violation content with a number
            content = self._add_violation_content(
                violation_data, content, violation_number=i + 1
            )

        # Add footer content (only once, after the last violation)
        content = self._add_footer_content(first_data, content)

        # Build the PDF
        doc.build(content)

        return output_path

    def generate_pdf(self, data):
        """
        Generate a PDF notice for a single violation.

        Args:
            data (dict): Violation data dictionary

        Returns:
            str: Path to the generated PDF file
        """
        # Generate a filename based on property address and date
        safe_address = (
            data["property_address"].replace(" ", "_").replace(",", "").replace(".", "")
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_address}_{timestamp}.pdf"
        output_path = os.path.join(self.output_dir, filename)

        # Create the PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        # Build the content
        content = []

        # Add header content
        content = self._add_header_content(data, content)

        # Add violation content
        content = self._add_violation_content(data, content)

        # Add footer content
        content = self._add_footer_content(data, content)

        # Build the PDF
        doc.build(content)

        return output_path
