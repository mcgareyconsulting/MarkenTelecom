import pandas as pd
import os
from pdf_generator.generate_pdf import ViolationNoticePDF

highland_mead_data = {
    "district_name": "Highlands Mead",
    "district_address_line1": "123 Highland Ave",
    "district_address_line2": "Suite 100",
    "district_phone": "555-123-4567",
}

highland_mead_rules = {
    "1.8 Vehicles, Repair": {
        "code": "1.8",
        "title": "Vehicles, Repair",
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
}

# Define field renaming
rename_map = {
    "Account Name": "homeowner_name",
    "ServiceAddress": "homeowner_address_line1",
    "Violation Date": "notice_date",
    "Violation Type": "violation_type",
    "Email": "homeowner_email",
    "Address": "property_address",
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


def collect_image(address):
    """
    Collects the image path for a given address.
    :param address: Address string to search for images
    """

    # remove all whitespace from address and convert to lowercase
    address = "".join(address.split())
    address = address.lower()

    # define the directory where images are stored
    image_dir = "../images"

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


generate_pdfs()
