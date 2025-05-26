from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
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
                - notice_date: Date of the notice
                - homeowner_name: Full name of the homeowner
                - homeowner_address_line1: First line of homeowner address
                - homeowner_address_line2: City, state, zip of homeowner
                - homeowner_email: Email address of homeowner
                - homeowner_salutation: Salutation for the letter (e.g., "Mr. Smith")
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
            "district_address_line1",
            "district_address_line2",
            "district_phone",
            "notice_date",
            "homeowner_name",
            "homeowner_address_line1",
            # "homeowner_address_line2",
            # "homeowner_email",
            # "homeowner_salutation",
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

        # District information
        district_info = f"""{data['district_name']}<br/>
                         {data['district_address_line1']}<br/>
                         {data['district_address_line2']}<br/>
                         {data['district_phone']}"""
        content.append(Paragraph(district_info, self.styles["DistrictInfo"]))

        # Notice title
        content.append(Paragraph("Courtesy Notice", self.styles["NoticeTitle"]))

        # Date
        content.append(Paragraph(data["notice_date"], self.styles["Date"]))

        # Recipient information
        recipient_info = f"""{data['homeowner_name']}<br/>
                          {data['homeowner_address_line1']}<br/>"""
        # {data['homeowner_address_line2']}"""
        content.append(Paragraph(recipient_info, self.styles["Recipient"]))

        # Email
        # content.append(
        #     Paragraph(
        #         f"Sent Via Email: {data['homeowner_email']}",
        #         self.styles["PropertyInfo"],
        #     )
        # )

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

        # Salutation
        # content.append(
        #     Paragraph(f"Dear: {data['homeowner_salutation']},", self.styles["Content"])
        # )

        # Letter content
        letter_content = f"""One of the primary responsibilities of {data['district_name']} ("the District") is to protect the aesthetic appeal and property values
        of the neighborhood. To accomplish this, certain Covenants and Design Guidelines have
        been established by which homeowners and residents must abide. During a recent
        inspection a concern was noted regarding your property and the District is asking for your
        help in achieving compliance."""
        content.append(Paragraph(letter_content, self.styles["Content"]))

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

        # Add violation image
        if os.path.exists(data["violation_image_path"]):
            img = Image(data["violation_image_path"], width=4 * inch, height=6 * inch)
            content.append(img)
            content.append(Paragraph("Violation Image", self.styles["ImageCaption"]))

        # Add regulation information
        regulation = data["regulation"]
        content.append(
            Paragraph(
                f"{regulation['code']} {regulation['title']}",
                self.styles["RegulationCode"],
            )
        )
        content.append(Paragraph(regulation["text"], self.styles["RegulationText"]))

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
        "notice_date": "May 24, 2025",
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
