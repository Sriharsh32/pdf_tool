document.getElementById('pdfForm').addEventListener('submit', async function(e) {
  e.preventDefault();

  const formData = new FormData();
  const files = document.getElementById('pdfFiles').files;
  const operation = document.getElementById('operation').value;
  const outputName = document.getElementById('outputName').value;
  const inputValue = document.getElementById('inputValue').value;
  const unitSelect = document.getElementById('unitSelect').value;

  for (let file of files) {
    formData.append("pdfFiles", file);
  }
  formData.append("operation", operation);
  formData.append("outputName", outputName);
  formData.append("inputValue", inputValue);
  formData.append("unitSelect", unitSelect);

  // Before formData is sent, set fromUnit and toUnit
  const unitSelectValue = document.getElementById('unitSelect').value;
  let fromUnit = '', toUnit = '';
  if (unitSelectValue) {
    [fromUnit, toUnit] = unitSelectValue.split('-');
  }
  formData.append("fromUnit", fromUnit);
  formData.append("toUnit", toUnit);

  try {
    const response = await fetch('http://127.0.0.1:5000/process', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}`);
    }

    const data = await response.json();
    const downloadSection = document.getElementById('downloadSection');
    const downloadList = document.getElementById('downloadList');
    downloadList.innerHTML = '';

    data.files.forEach(file => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = `http://127.0.0.1:5000${file.url}`;
      a.textContent = `Download ${file.name}`;
      a.download = file.name;
      li.appendChild(a);
      downloadList.appendChild(li);
    });

    downloadSection.style.display = 'block';
  } catch (error) {
    console.error("Error processing files:", error);
    alert("Failed to process files. Please try again.");
  }
});

// Unit Conversion Logic
const unitConversions = {
  "mm-inch": 0.03937,
  "cm-inch": 0.3937,
  "cm-feet": 0.0328,
  "m-feet": 3.2808,
  "km-miles": 0.6214,
  "inch-mm": 25.4,
  "inch-cm": 2.54,
  "feet-m": 0.3048,
  "miles-km": 1.609
};

document.getElementById('unitSelect').addEventListener('change', function () {
  const selectedConversion = this.value;
  const inputValue = document.getElementById('inputValue').value;
  const resultDisplay = document.getElementById('convertedValue');

  if (!inputValue || isNaN(parseFloat(inputValue))) {
    resultDisplay.textContent = "Enter a valid number!";
    return;
  }

  const value = parseFloat(inputValue);

  // Corrected unit conversion logic
  const unitConversions = {
    "mm-inch": value / 25.4,         // Millimeters to Inches
    "cm-inch": value / 2.54,         // Centimeters to Inches
    "cm-feet": value / 30.48,        // Centimeters to Feet
    "m-feet": value * 3.28084,       // Meters to Feet
    "km-miles": value * 0.621371,    // Kilometers to Miles
    "inch-mm": value * 25.4,         // Inches to Millimeters
    "inch-cm": value * 2.54,         // Inches to Centimeters
    "feet-m": value / 3.28084,       // Feet to Meters
    "miles-km": value / 0.621371     // Miles to Kilometers
  };

  if (unitConversions[selectedConversion] !== undefined) {
    resultDisplay.textContent = `Converted Value: ${unitConversions[selectedConversion].toFixed(4)}`;
  } else {
    resultDisplay.textContent = "Select a valid unit conversion!";
  }
});