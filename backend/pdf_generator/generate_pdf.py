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
)
from reportlab.lib.units import inch
from datetime import datetime
import os
from PIL import Image as PILImage, ExifTags
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

    def _fetch_and_prepare_image(self, image_url, max_width=300, max_height=450):
        """
        Fetch image from URL, apply EXIF orientation, scale to fit max dimensions,
        and return ReportLab Image flowable.
        """

        # Fetch image bytes
        response = requests.get(image_url)
        response.raise_for_status()
        img_data = response.content

        # Open with PIL for processing
        pil_img = PILImage.open(io.BytesIO(img_data))

        # Apply EXIF orientation (fix rotation for mobile photos)
        try:
            for orientation in ExifTags.TAGS.keys():
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
            # No EXIF or no orientation tag, ignore silently
            pass

        # Scale while keeping aspect ratio
        width, height = pil_img.size
        ratio = min(max_width / width, max_height / height, 1)  # don't upscale

        new_width = int(width * ratio)
        new_height = int(height * ratio)

        pil_img = pil_img.resize((new_width, new_height), PILImage.LANCZOS)

        # Save back to bytes buffer
        output_buffer = io.BytesIO()
        pil_img.save(output_buffer, format="PNG")
        output_buffer.seek(0)

        # Create ReportLab Image flowable
        reportlab_img = Image(output_buffer, width=new_width, height=new_height)
        reportlab_img.hAlign = "CENTER"

        return reportlab_img

    def generate_pdf(self, data):
        """
        Generate a PDF violation notice using the provided data.

        Args:
            data (dict): Dictionary containing all required fields for the PDF
                Required keys:
                - district_name: Name of the metropolitan district
                - district_address_line1: First line of district address
                - district_address_line2: Second line of district address
                - district_phone: District phone number
                - notice_date: Date of the notice (can be string, datetime, or pandas Timestamp)
                - homeowner_name: Full name of the homeowner
                - homeowner_address_line1: First line of homeowner address
                - homeowner_address_line2: City, state, zip of homeowner (optional)
                - homeowner_email: Email address of homeowner (optional)
                - homeowner_salutation: Salutation for the letter (optional)
                - property_address: Address of the property in violation
                - violation_type: Type of violation
                - violation_image_path: Path to the image showing the violation
                - regulation: Dictionary containing regulation information with keys:
                  - code: Regulation code (e.g., "2.26")
                  - title: Regulation title (e.g., "Landscaping")
                  - text: Full text of the regulation

        Returns:
            str: Path to the generated PDF file
        """
        # Ensure all required fields are present
        required_fields = [
            "district_name",
            "notice_date",
            "homeowner_name",
            "mailing_address",
            "mailing_city_st_zip",
            "property_address",
            "violation_type",
            "violation_images",
            "regulation",
        ]

        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Check regulation dictionary structure
        regulation_fields = ["title", "description"]
        for field in regulation_fields:
            if field not in data["regulation"]:
                raise ValueError(f"Missing regulation field: {field}")

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

        # District name (large and blue)
        content.append(Paragraph(data["district_label"], self.styles["DistrictName"]))

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
            content.append(
                Paragraph(
                    f"Sent Via Email: {data['homeowner_email']}",
                    self.styles["PropertyInfo"],
                )
            )

        # Property and violation information
        content.append(
            Paragraph(
                f"Property: {data['property_address']}", self.styles["PropertyInfo"]
            )
        )
        # content.append(
        #     Paragraph(
        #         f"Violation: {data['violation_type']}", self.styles["ViolationInfo"]
        #     )
        # )

        # Salutation if available
        if "homeowner_salutation" in data and data["homeowner_salutation"]:
            content.append(
                Paragraph(
                    f"Dear: {data['homeowner_salutation']},", self.styles["Content"]
                )
            )

        # Letter content
        letter_content = f"""One of the primary responsibilities of {data['district_label']} ("the District") is to protect the aesthetic appeal and property values
        of the neighborhood. To accomplish this, certain Covenants and Design Guidelines have
        been established by which homeowners and residents must abide. During a recent
        inspection a concern was noted regarding your property and the District is asking for your
        help in achieving compliance."""
        content.append(Paragraph(letter_content, self.styles["Content"]))

        # Add regulation information
        regulation = data["regulation"]
        content.append(
            Paragraph(
                f"{regulation['title']}",
                self.styles["RegulationCode"],
            )
        )
        content.append(
            Paragraph(regulation["description"], self.styles["RegulationText"])
        )

        # Add violation image with EXIF orientation handling
        violation_image = data["violation_images"][0]  # Simplified for one image

        print(f"Processing image: {violation_image['file_path']}")

        try:
            img = self._fetch_and_prepare_image(violation_image["file_path"])
            content.append(img)
            content.append(Paragraph("Violation Image", self.styles["ImageCaption"]))
        except Exception as e:
            print(f"Failed to fetch or process image: {e}")
            content.append(
                Paragraph("No violation image available.", self.styles["ImageCaption"])
            )
        content.append(
            Paragraph(
                """We ask that you remedy this matter within the next 30 days from the date of this letter.
        Failure to do so may result in potential fines per the governing documents.""",
                self.styles["Content"],
            )
        )

        content.append(
            Paragraph(
                """If you have already resolved the above matter, we thank you for your prompt attention and
        appreciate your help keeping the neighborhood looking its best.""",
                self.styles["Content"],
            )
        )

        # Closing
        content.append(Paragraph("Sincerely,", self.styles["Closing"]))
        content.append(Paragraph(data["district_label"], self.styles["Signature"]))

        # Build the PDF
        doc.build(content)

        return output_path


def test_template():
    """Test the template with sample data."""
    # Create sample data with regulation text
    sample_data = {
        "district_name": "Saddler Ridge Metropolitan District",
        "district_address_line1": "c/o Public Alliance LLC",
        "district_address_line2": "7555 E. Hampden Ave., Suite 501",
        "district_phone": "(720) 213-6621",
        "notice_date": "20-May",
        "homeowner_name": "Mr. John Doe",
        "homeowner_address_line1": "123 Sample Street",
        "homeowner_address_line2": "Anytown, CO 80000",
        "homeowner_email": "johndoe@example.com",
        "homeowner_salutation": "Mr. Doe",
        "property_address": "123 Sample Street, Anytown, CO 80000",
        "violation_type": "Fence Rails",
        "violation_image_path": "/home/ubuntu/pdf_analysis/image-002.jpg",
        "regulation": {
            "code": "2.26",
            "title": "Landscaping",
            "text": "Landscaping must be kept at all times in a neat, healthy, weed-free, and attractive condition.",
        },
    }

    # Generate the PDF
    generator = ViolationNoticePDF()
    pdf_path = generator.generate_pdf(sample_data)

    print(f"Test PDF generated at: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    test_template()
