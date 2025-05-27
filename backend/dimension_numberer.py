import fitz  # PyMuPDF
import re

def number_dimensions(input_pdf_path, output_pdf_path):
    doc = fitz.open(input_pdf_path)

    # Regex: match only dimensions (⌀12, R5, 45°, 100), not tolerances (±, +, - after number)
    dimension_pattern = re.compile(
        r'(⌀\s*\d+(?:\.\d+)?\b|R\s*\d+(?:\.\d+)?\b|\d+(?:\.\d+)?\s*°|\b\d+(?:\.\d+)?\b)'
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
    annotated_areas = []

    for i, (page_num, rect, text) in enumerate(all_blocks):
        dim_matches = list(dimension_pattern.finditer(text))
        filtered_dims = []
        for match in dim_matches:
            dim = match.group()
            start, end = match.span()
            # Get context around the match
            before = text[max(0, start-2):start]
            after = text[end:end+2]
            # Exclude if part of tolerance or fit (e.g., ±, +, -, (, ), etc)
            if any(sym in after for sym in ['±', '+', '-', '(', ')']) or any(sym in before for sym in ['±', '+', '-', '(', ')']):
                continue
            filtered_dims.append(dim)
        if not filtered_dims:
            continue

        for dim in filtered_dims:
            # Extract symbol and value
            if dim.startswith('⌀') or dim.startswith('R'):
                symbol = dim[0]
                value = re.findall(r'\d+(?:\.\d+)?', dim)
            elif '°' in dim:
                symbol = '°'
                value = re.findall(r'\d+(?:\.\d+)?', dim)
            else:
                symbol = ''
                value = re.findall(r'\d+(?:\.\d+)?', dim)

            if not value:
                continue

            try:
                nominal = float(value[0])
            except ValueError:
                continue

            # No tolerance extraction here
            low_tol = up_tol = 0.0
            tolerance_type = "No Tolerance"

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

            # Annotate PDF without overlap
            page = doc[page_num - 1]
            number_text = str(serial_counter)
            font_size = 20
            vertical_gap = font_size * 1.7  # More gap between numbers
            char_width = font_size * 0.7    # Slightly wider for safety
            text_width = len(number_text) * char_width
            center_x = rect.x0 + (rect.width / 2) - (text_width / 2)

            max_attempts = 15  # Try more positions
            for offset_idx in range(max_attempts):
                offset_y = vertical_gap * (offset_idx + 1)
                above_y = rect.y0 - offset_y
                insert_point = fitz.Point(center_x, above_y)
                # Make annotation area larger for better overlap detection
                annot_rect = fitz.Rect(
                    insert_point.x - 4, insert_point.y - 4,
                    insert_point.x + text_width + 4,
                    insert_point.y + font_size + 4
                )

                if not any(annot_rect.intersects(existing) for existing in annotated_areas):
                    page.insert_text(
                        insert_point,
                        number_text,
                        fontname="helv",
                        fontsize=font_size,
                        color=(1, 0, 0)
                    )
                    annotated_areas.append(annot_rect)
                    break

            serial_counter += 1

    doc.save(output_pdf_path)
