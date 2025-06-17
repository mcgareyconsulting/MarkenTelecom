from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from collections import Counter
from datetime import datetime
from reportlab.platypus import Image as RLImage
from PIL import Image as PILImage, ExifTags, ImageEnhance, ImageFilter
import io
import requests
import os


def _fetch_and_prepare_image(
    image_url, max_width=180, max_height=240, quality=95, sharpen_factor=1.3
):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        img_data = response.content

        pil_img = PILImage.open(io.BytesIO(img_data))

        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")

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
            pass

        width, height = pil_img.size
        ratio = min(max_width / width, max_height / height, 1)
        new_width = int(width * ratio)
        new_height = int(height * ratio)

        if width > new_width * 2 or height > new_height * 2:
            intermediate_width = int(new_width * 1.5)
            intermediate_height = int(new_height * 1.5)
            intermediate_img = pil_img.resize(
                (intermediate_width, intermediate_height), PILImage.LANCZOS
            )
            pil_img = intermediate_img.resize((new_width, new_height), PILImage.LANCZOS)
        else:
            pil_img = pil_img.resize((new_width, new_height), PILImage.LANCZOS)

        if sharpen_factor > 1.0:
            pil_img = pil_img.filter(ImageFilter.GaussianBlur(radius=0.5))
            enhancer = ImageEnhance.Sharpness(pil_img)
            pil_img = enhancer.enhance(sharpen_factor)

        output_buffer = io.BytesIO()
        pil_img.save(output_buffer, format="PNG", optimize=True)
        output_buffer.seek(0)

        reportlab_img = RLImage(output_buffer, width=new_width, height=new_height)
        reportlab_img.hAlign = "CENTER"

        return reportlab_img
    except Exception as e:
        print(f"Error processing image: {e}")
        return None


def generate_board_report(output_path, district_name, violations, date=None):
    if date is None:
        date = datetime.now().strftime("%B %d, %Y")

    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph(
        f"<b>{district_name} – Covenant Inspection Results {date}</b>", styles["Title"]
    )
    elements.append(title)
    elements.append(Spacer(1, 12))

    # inspection_types = ["courtesy", "fine", "warning", "resolved"]
    # inspection_counts = Counter(v["inspection_type"] for v in violations)
    # table_data = [["Courtesy", "Fine", "Warning", "Resolved"]] + [
    #     [
    #         inspection_counts.get("courtesy", 0),
    #         inspection_counts.get("fine", 0),
    #         inspection_counts.get("warning", 0),
    #         inspection_counts.get("resolved", 0),
    #     ]
    # ]
    courtesy_count = len(violations)
    table_data = [["Courtesy", "Fine", "Warning", "Resolved"]] + [
        [courtesy_count, 0, 0, 0]
    ]
    table = Table(table_data, colWidths=[100] * 4)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 20))

    violation_counts = Counter(v["violation_type"] for v in violations)
    drawing = Drawing(400, 200)
    bar_chart = VerticalBarChart()
    bar_chart.x = 50
    bar_chart.y = 30
    bar_chart.height = 150
    bar_chart.width = 300
    bar_chart.data = [list(violation_counts.values())]
    bar_chart.categoryAxis.categoryNames = list(violation_counts.keys())
    bar_chart.barWidth = 15
    bar_chart.groupSpacing = 10
    bar_chart.bars.fillColor = colors.darkblue
    drawing.add(bar_chart)
    elements.append(drawing)
    elements.append(Spacer(1, 20))

    row_width = 2
    images = []

    for v in violations:
        for image_info in v.get("violation_images", []):
            img = _fetch_and_prepare_image(image_info["file_path"])
            if img:
                images.append(img)

    for i in range(0, len(images), row_width):
        row = images[i : i + row_width]
        elements.extend(row)
        elements.append(Spacer(1, 12))

    doc.build(elements)
