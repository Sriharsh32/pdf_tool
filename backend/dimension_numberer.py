import fitz  # PyMuPDF
import re
import pandas as pd

def number_dimensions(input_pdf_path, output_pdf_path,):
    doc = fitz.open(input_pdf_path)

    # Universal dimension pattern for engineering drawings
    dimension_pattern = re.compile(
        r'(⌀\s*\d+(?:\.\d+)?|'         # Diameter
        r'R\s*\d+(?:\.\d+)?|'          # Radius
        r'\d+(?:\.\d+)?\s*°|'          # Angle
        r'\d+(?:\.\d+)?'               # Linear
        r')'
    )

    all_blocks = []
    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("blocks", sort=True)
        for block in blocks:
            text = block[4].strip().replace("−", "-")
            rect = fitz.Rect(block[:4])
            all_blocks.append((page_num, rect, text))

    serial_counter = 1
    data = []

    for i, (page_num, rect, text) in enumerate(all_blocks):
        dim_matches = dimension_pattern.findall(text)
        if not dim_matches:
            continue

        for dim in dim_matches:
            # Ensure dim is a string and handle it accordingly
            if isinstance(dim, str):
                dim = dim.strip()
            else:
                continue  # Skip if dim is not a string

            # The rest of your processing logic remains unchanged
            if dim.startswith('⌀') or dim.startswith('R'):
                symbol = dim[0]
                value = dim[1:].strip()
            elif '°' in dim:
                symbol = '°'
                value = dim.replace('°', '').strip()
            else:
                symbol = ''
                value = dim.replace('(', '').replace(')', '').split()[0]

            try:
                nominal = float(value)
            except ValueError:
                continue

            low_tol = up_tol = 0.0
            tolerance_type = "No Tolerance"

            for j, (p2, r2, t2) in enumerate(all_blocks):
                if j == i or p2 != page_num:
                    continue

                if r2.intersects(rect + (-50, -30, 250, 50)):
                    t2 = t2.replace("−", "-")

                    if "±" in t2:
                        try:
                            tol_val = float(t2.replace('±', '').strip())
                            low_tol = -tol_val
                            up_tol = tol_val
                            tolerance_type = "Symmetric (±)"
                            break
                        except ValueError:
                            continue

                    parts = re.findall(r'[+-]?\d+(?:\.\d+)?', t2)
                    if len(parts) == 2:
                        try:
                            low_tol = float(parts[0])
                            up_tol = float(parts[1])
                            tolerance_type = "Asymmetric (+/-)"
                            break
                        except ValueError:
                            continue

            lower_bound = nominal + low_tol
            upper_bound = nominal + up_tol

            data.append({
                "Serial Number": serial_counter,
                "Value": nominal,
                "Symbol": symbol,
                "Tolerance Type": tolerance_type,
                "Lower Tol": low_tol,
                "Upper Tol": up_tol,
                "Lower Bound": round(lower_bound, 3),
                "Upper Bound": round(upper_bound, 3),
                "Page": page_num,
                "Rect": rect
            })

            # Annotate PDF
            page = doc[page_num - 1]
            number_text = str(serial_counter)
            font_size = 10
            vertical_gap = font_size * 1.2
            char_width = font_size * 0.5
            text_width = len(number_text) * char_width
            center_x = rect.x0 + (rect.width / 2) - (text_width / 2)
            above_y = rect.y0 - vertical_gap
            insert_point = fitz.Point(center_x, above_y)
            page.insert_text(
                insert_point,
                number_text,
                fontname="helv",
                fontsize=font_size,
                color=(1, 0, 0)
            )

            serial_counter += 1

    doc.save(output_pdf_path)

