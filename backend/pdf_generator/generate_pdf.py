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
from PIL import Image as PILImage
import io


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

    def _process_image_with_exif(
        self, image_path, max_width=5.5 * inch, max_height=4 * inch
    ):
        """
        Process an image with EXIF orientation data and return properly oriented image data
        with appropriate dimensions for the PDF.

        Args:
            image_path: Path to the image file
            max_width: Maximum width for the image in the PDF
            max_height: Maximum height for the image in the PDF

        Returns:
            tuple: (image_data, width, height) where image_data is bytes and width/height are in points
        """
        try:
            # Open the image and apply EXIF orientation
            with PILImage.open(image_path) as img:
                # Check if the image has EXIF data
                exif = None
                if hasattr(img, "_getexif") and img._getexif() is not None:
                    exif = dict(img._getexif().items())

                # Apply orientation based on EXIF data if available
                if exif and 274 in exif:  # 274 is the EXIF orientation tag
                    orientation = exif[274]

                    # Apply rotation based on orientation
                    if orientation == 2:
                        img = img.transpose(PILImage.FLIP_LEFT_RIGHT)
                    elif orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 4:
                        img = img.rotate(180, expand=True).transpose(
                            PILImage.FLIP_LEFT_RIGHT
                        )
                    elif orientation == 5:
                        img = img.rotate(-90, expand=True).transpose(
                            PILImage.FLIP_LEFT_RIGHT
                        )
                    elif orientation == 6:
                        img = img.rotate(-90, expand=True)
                    elif orientation == 7:
                        img = img.rotate(90, expand=True).transpose(
                            PILImage.FLIP_LEFT_RIGHT
                        )
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)

                # Force portrait orientation for mobile photos if height > width
                img_width, img_height = img.size
                if img_height > img_width:
                    # Already in portrait orientation, no need to rotate
                    pass

                # Calculate aspect ratio
                aspect_ratio = img_width / img_height

                # Determine if image is portrait or landscape after any rotation
                is_portrait = img_height > img_width

                if is_portrait:
                    # For portrait images, limit height and calculate width
                    # Use a smaller max_height for portrait to avoid excessive page usage
                    portrait_max_height = 3.5 * inch
                    new_height = min(portrait_max_height, max_height)
                    new_width = new_height * aspect_ratio

                    # If width is still too large, scale down further
                    if new_width > max_width:
                        new_width = max_width
                        new_height = new_width / aspect_ratio
                else:
                    # For landscape images, limit width and calculate height
                    new_width = min(max_width, max_width)
                    new_height = new_width / aspect_ratio

                    # If height is still too large, scale down further
                    if new_height > max_height:
                        new_height = max_height
                        new_width = new_height * aspect_ratio

                # Save the processed image to a bytes buffer
                img_buffer = io.BytesIO()
                img.save(img_buffer, format=img.format or "JPEG")
                img_data = img_buffer.getvalue()

                return img_data, new_width, new_height

        except Exception as e:
            # If there's an error processing the image, return the original path and default dimensions
            print(f"Error processing image with EXIF: {e}")
            return None, max_width, max_height

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
            "homeowner_address_line1",
            "homeowner_city_st_zip",
            "property_address",
            "violation_type",
            "violation_image_path",
            "regulation",
        ]

        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Check regulation dictionary structure
        regulation_fields = ["code", "title", "text"]
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
        content.append(Paragraph(data["district_name"], self.styles["DistrictName"]))

        # District address block (standard style)
        district_address_block = """c/o Public Alliance LLC<br/>
                         7555 E. Hampden Ave., Suite 501<br/>
                         Denver, CO 80231<br/>
                         (720) 213-6621"""
        content.append(Paragraph(district_address_block, self.styles["DistrictInfo"]))

        # Notice title
        content.append(Paragraph("Courtesy Notice", self.styles["NoticeTitle"]))

        # Format the date to ensure it's a string
        formatted_date = self._format_date(data["notice_date"])
        content.append(Paragraph(formatted_date, self.styles["Date"]))

        # Recipient information
        recipient_info = f"""{data['homeowner_name']}<br/>
                          {data['homeowner_address_line1']}<br/>
                          {data['homeowner_city_st_zip']}"""

        # Add second address line if available
        if "homeowner_address_line2" in data and data["homeowner_address_line2"]:
            recipient_info += f"<br/>{data['homeowner_address_line2']}"

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
        content.append(
            Paragraph(
                f"Violation: {data['violation_type']}", self.styles["ViolationInfo"]
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
        letter_content = f"""One of the primary responsibilities of {data['district_name']} ("the District") is to protect the aesthetic appeal and property values
        of the neighborhood. To accomplish this, certain Covenants and Design Guidelines have
        been established by which homeowners and residents must abide. During a recent
        inspection a concern was noted regarding your property and the District is asking for your
        help in achieving compliance."""
        content.append(Paragraph(letter_content, self.styles["Content"]))

        # Add regulation information
        regulation = data["regulation"]
        content.append(
            Paragraph(
                f"{regulation['code']} {regulation['title']}",
                self.styles["RegulationCode"],
            )
        )
        content.append(Paragraph(regulation["text"], self.styles["RegulationText"]))

        # Add violation image with EXIF orientation handling
        if os.path.exists(data["violation_image_path"]):
            # Process the image with EXIF orientation
            img_data, img_width, img_height = self._process_image_with_exif(
                data["violation_image_path"]
            )

            if img_data:
                # Create the image from processed data
                img = Image(io.BytesIO(img_data), width=img_width, height=img_height)
            else:
                # Fallback to original path if processing failed
                img = Image(
                    data["violation_image_path"], width=img_width, height=img_height
                )

            # Center the image
            img.hAlign = "CENTER"

            content.append(img)
            content.append(Paragraph("Violation Image", self.styles["ImageCaption"]))

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
        content.append(Paragraph(data["district_name"], self.styles["Signature"]))

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
