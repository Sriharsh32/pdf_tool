import fitz  # PyMuPDF
import re
import pandas as pd

def extract_all_tolerances_to_df(pdf_path):
    doc = fitz.open(pdf_path)
    all_data = []

    # Tolerance patterns
    tolerance_patterns = [
        (r"(⌀\d+(?:\.\d+)?)[ ]*([a-zA-Z]+\d+)?\s*\(\s*([+-]?\d*\.?\d+)\s*([+-]?\d*\.?\d+)\s*\)", "Fit Tolerance"),
        (r"(\d+(?:\.\d+)?)\s*([a-zA-Z]+\d+)\s*\(\s*([+-]?\d*\.?\d+)\s*([+-]?\d*\.?\d+)\s*\)", "Fit Tolerance"),
        (r"(⌀\d+(?:\.\d+)?)±(\d*\.?\d+)", "Symmetric Tolerance"),
        (r"(\d+(?:\.\d+)?)\s*\+(\d*\.?\d+)\s*([+-]\d*\.?\d+)", "Asymmetric Tolerance"),
        (r"(⌀\d+(?:\.\d+)?)\s*([a-zA-Z]+\d+)\s*\(\s*([+-]?\d*\.?\d+)\s*([+-]?\d*\.?\d+)\s*\)", "Fit Tolerance")
    ]

    for page in doc:
        text = page.get_text()
        for pattern, tol_type in tolerance_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                all_data.append((tol_type,) + match)

    # Normalize data
    columns = ["Type", "Raw Dimension", "Fit/Class", "Upper Tol", "Lower Tol"]
    normalized_data = [list(row) + [''] * (5 - len(row)) for row in all_data]
    df = pd.DataFrame(normalized_data, columns=columns)
    df.insert(0, "Serial No", range(1, len(df) + 1))

    # Parse values and bounds
    nominal_vals, dim_types, lower_bounds, upper_bounds = [], [], [], []

    for _, row in df.iterrows():
        dim_raw, upper, lower = row["Raw Dimension"], row["Upper Tol"], row["Lower Tol"]

        if dim_raw.startswith("⌀"):
            dim_type = "Diameter"
            nominal = float(dim_raw[1:]) if dim_raw[1:].replace('.', '', 1).isdigit() else None
        elif dim_raw.startswith("R"):
            dim_type = "Radius"
            nominal = float(dim_raw[1:]) if dim_raw[1:].replace('.', '', 1).isdigit() else None
        else:
            dim_type = "Linear"
            nominal = float(dim_raw) if dim_raw.replace('.', '', 1).isdigit() else None

        try:
            lower_tol = float(lower)
        except:
            lower_tol = 0.0
        try:
            upper_tol = float(upper)
        except:
            upper_tol = 0.0

        lower_bounds.append(nominal + lower_tol if nominal is not None else None)
        upper_bounds.append(nominal + upper_tol if nominal is not None else None)
        nominal_vals.append(nominal)
        dim_types.append(dim_type)

    df["Nominal"] = nominal_vals
    df["Dimension Type"] = dim_types
    df["Lower Bound"] = lower_bounds
    df["Upper Bound"] = upper_bounds
    return df.drop_duplicates(subset=["Raw Dimension", "Fit/Class", "Upper Tol", "Lower Tol"])
