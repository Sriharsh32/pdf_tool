from flask import Flask, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
from backend.tolerance_extractor import extract_all_tolerances_to_df
from backend.dimension_numberer import number_dimensions

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/process', methods=['POST'])
def process_files():
    operation = request.form.get('operation')
    output_name = request.form.get('outputName') or "output"
    from_unit = request.form.get('fromUnit')
    to_unit = request.form.get('toUnit')
    uploaded_files = request.files.getlist("pdfFiles")
    output_files = []

    for file in uploaded_files:
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        if operation == "numbering":
            output_file = os.path.join(OUTPUT_FOLDER, f"{output_name}.pdf")
            number_dimensions(input_path, output_file)
        elif operation == "tolerance":
            output_file = os.path.join(OUTPUT_FOLDER, f"{output_name}.xlsx")
            df = extract_all_tolerances_to_df(input_path)
            df.to_excel(output_file, index=False)
        else:
            return jsonify({"error": "Invalid operation"}), 400

        output_files.append({
            "name": os.path.basename(output_file),
            "url": f"/downloads/{os.path.basename(output_file)}"
        })

    return jsonify({"files": output_files})

@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
