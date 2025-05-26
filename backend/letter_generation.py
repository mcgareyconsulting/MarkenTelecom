import pandas as pd
import os
from pdf_generator.generate_pdf import ViolationNoticePDF
import re
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

highland_mead_data = {
    "district_name": "Highlands Mead Metro District",
}

highland_mead_rules = {
    "1.8 Vehicle Repair": {
        "code": "1.8",
        "title": "Vehicle Repair",
        "text": (
            "No activity such as, but not limited to, maintenance, repair, rebuilding, dismantling, repainting or "
            "servicing of any kind of vehicles, trailers or boats, may be performed or conducted in the Community "
            "unless it is done within a completely enclosed structure that screens the sight and sound of the activity "
            "from the street, alley, and from adjoining property. The foregoing restriction shall not be deemed to "
            "prevent the washing and polishing of any motor vehicle, boat, trailer, motor cycle, or other vehicle, "
            "together with those activities normally incident and necessary to such washing and polishing on a Lot."
        ),
    },
    "2.49 Trash Containers": {
        "code": "2.49",
        "title": "Trash Containers",
        "text": (
            "Trash containers shall only be placed at curbside for pickup after 6:00 p.m. on the day before pick-up and "
            "shall be returned to a proper storage location by 9:00 p.m. the day of pick-up. Trash containers shall be "
            "stored out of sight at all times except on the day of pickup, and shall be kept in a clean and sanitary condition."
        ),
    },
    "2.26 Landscaping": {
        "code": "2.26",
        "title": "Landscaping",
        "text": (
            "Landscaping must be kept at all times in a neat, healthy, weed-free, and attractive condition."
        ),
    },
    "2.51 Unsightly Conditions": {
        "code": "2.51",
        "title": "Unsightly Conditions",
        "text": (
            "No unsightly articles or conditions shall be permitted to remain or accumulate on any Lot. By way of example, "
            "but not limitation, such items could include rock or mulch piles, construction materials, abandoned toys, "
            "inoperable vehicles, dead or dying landscaping, peeling or faded paint, gardening equipment not in actual use, "
            "fencing in disrepair, etc."
        ),
    },
}

# Define field renaming
rename_map = {
    "Account Name": "homeowner_name",
    "MailAddressLine1": "homeowner_address_line1",
    "MailCity": "homeowner_city",
    "MailState": "homeowner_state",
    "MailZip": "homeowner_zip",
    "Violation Date": "notice_date",
    "Violation Type": "violation_type",
    "Email": "homeowner_email",
    "PropertyAddressLine1": "property_address",
}


def read_dataset(
    filename="../datasets/HighlandsMead5-20Data.xlsx",
):
    """
    Reads the HighlandsMead Excel file and returns a pandas DataFrame.
    :param filename: Path to the Excel file (default: datasets/HighlandsMead.xlsx)
    :return: pandas DataFrame or None if file not found/error
    """
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return None
    try:
        df = pd.read_excel(filename)
        print(f"Loaded {len(df)} rows from {filename}")
        return df
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return None


def clean_address(address):
    """
    Removes trailing periods from common street abbreviations (e.g., 'St.' -> 'St').
    """
    # List of common abbreviations (add more as needed)
    abbreviations = [
        "st",
        "ave",
        "blvd",
        "dr",
        "rd",
        "ln",
        "ct",
        "pl",
        "trl",
        "pkwy",
        "cir",
        "ter",
        "way",
    ]
    # Regex: replace abbreviation with period at end of word with no period
    pattern = re.compile(
        r"\b(" + "|".join(abbreviations) + r")\.(?=\s|$)", re.IGNORECASE
    )
    return pattern.sub(lambda m: m.group(1), address)


def collect_image(address):
    """
    Collects the image path for a given address.
    :param address: Address string to search for images
    """

    # remove all whitespace from address, remove punctuation, convert to lowercase
    address = clean_address(address)
    address = "".join(address.split())
    address = address.lower()

    # define the directory where images are stored
    image_dir = "../images/HighlandsMead"

    # find all images in the directory that match the address
    images = [
        os.path.join(image_dir, f)
        for f in os.listdir(image_dir)
        if address.lower() in f.lower()
        and f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    # return the image page
    if images:
        image_path = images[0]  # Take the first matching image
        print(f"Image found for {address}: {image_path}")
        return image_path
    else:
        print(f"No image found for {address}")
        return None


def generate_pdfs():
    """
    Function to generate PDFs based on the Highland Mead rules and dataset.
    This function reads the dataset, applies the rules, and generates PDF files for each address.
    """

    df = read_dataset()
    if df is None:
        print("No data to process.")
        return

    # # collect addrresses for Avery 48807 labels
    # addresses = []
    # for index, row in df.iterrows():
    #     {
    #         "name": row.get("Account Name", "N/A"),
    #         "street": row.get("MailAddressLine1", "N/A"),
    #         "city": row.get("MailCity", "N/A"),
    #         "state": row.get("MailState", "N/A"),
    #         "zip": row.get("MailZip", "N/A"),
    #     }

    # # send to Avery 48807 labels
    # create_avery_48807_labels(addresses)

    # strip trailing whitespace from column names
    df.columns = df.columns.str.strip()

    for index, row in df.iterrows():
        # Filter condition (e.g., only if 'Violation' is not empty)
        if pd.isna(row.get("Violation Type")) or pd.isna(row.get("Account Name")):
            continue  # Skip invalid/incomplete rows

        # Build renamed dictionary
        data_dict = {
            new_key: row[old_key]
            for old_key, new_key in rename_map.items()
            if pd.notna(row.get(old_key))
        }

        # add highland_mead_data to data_dict
        data_dict.update(highland_mead_data)

        # match violation type with regulations
        data_dict["regulation"] = highland_mead_rules[row.get("Code")]

        # collect image path for violation
        data_dict["violation_image_path"] = collect_image(data_dict["property_address"])

        # If no image is found, skip PDF generation for this row
        if not data_dict["violation_image_path"]:
            print(
                f"Skipping PDF generation for {data_dict['property_address']} (no image found)."
            )
            continue

        # convert notice date to string
        if pd.notna(data_dict.get("notice_date")):
            data_dict["notice_date"] = data_dict["notice_date"].strftime("%Y-%m-%d")
        else:
            data_dict["notice_date"] = "N/A"

        # Create PDF generator
        generator = ViolationNoticePDF()

        # Generate PDF
        pdf_path = generator.generate_pdf(data_dict)
        print(f"PDF generated at: {pdf_path}")


def create_avery_48807_labels(addresses, output_file="avery_48807_labels.docx"):
    """
    Function to create Avery 48807 labels in a Word document.
    :param addresses: List of address dictionaries with keys: name, street, city, state, zip
    """
    doc = Document()

    labels_per_page = 10  # 2 cols × 5 rows
    per_row = 2
    per_col = 5

    chunks = [
        addresses[i : i + labels_per_page]
        for i in range(0, len(addresses), labels_per_page)
    ]

    for page in chunks:
        table = doc.add_table(rows=per_col, cols=per_row)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        # Set column widths and height approximations
        for row in table.rows:
            for cell in row.cells:
                cell.width = Inches(4)
                cell.height = Inches(2)
                cell.paragraphs[0].paragraph_format.alignment = (
                    WD_PARAGRAPH_ALIGNMENT.LEFT
                )

        i = 0
        for row in table.rows:
            for cell in row.cells:
                if i < len(page):
                    a = page[i]
                    label = f"{a['name']}\n{a['street']}\n{a['city']}, {a['state']} {a['zip']}"
                    p = cell.paragraphs[0]
                    run = p.add_run(label)
                    run.font.size = Pt(12)
                    i += 1
                else:
                    cell.text = ""

        doc.add_page_break()

    doc.save(output_file)
    print(f"Saved Avery 48807 label file as: {output_file}")


generate_pdfs()
