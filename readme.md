# Motor Insurance PDF Data Extraction

<!-- markdownlint-disable -->

## Overview
This project extracts key information from **Motor Insurance Policy PDFs** and converts it into a **structured JSON format** following a **strict predefined schema**.  
The solution is designed to handle **non-uniform, semi-structured PDFs** reliably and produce consistent output for downstream systems.

---

## Problem Statement
Motor insurance policy documents are provided in PDF format and contain important customer, vehicle, policy, and premium details in varying layouts.

The objective is to:
- Extract required fields accurately
- Output a valid JSON object with **all predefined keys**
- Ensure consistency, correctness, and robustness across different PDF in any format.
---

## Output Schema
For **every input PDF**, the output must be **one JSON object** containing **all keys** listed below.

- All keys must always be present  
- If a value is missing or not found, return an empty string `""`  
- No additional or missing keys are allowed  

---

## Approach (WHAT WE WILL DO)

### 1. PDF Text Extraction
- Read PDF content using a PDF parsing library
- Use OCR if the PDF is scanned or image-based

### 2. Keyword-Based Detection
- Identify fields using **labels and keywords** instead of fixed positions
- This helps handle layout variations across different insurers

### 3. Field Mapping
- Map each schema key to its corresponding keyword(s) in the PDF
- Example:
  - `POLICY_NO` → “Policy No”
  - `CUSTOMER_NAME` → “Insured Name”


### 4. Data Cleaning & Formatting
- Normalize date formats
- Extract numeric values without extra text
- Merge multi-line fields like addresses and nominee details

### 5. Missing Data Handling
- If a field is not found, assign `""` (null)
- Ensure output structure is never broken

### 6. JSON Generation
- Generate a valid JSON object
- Maintain strict schema discipline

---

## Key Features
- Handles multiple PDF layouts  
- Strict schema enforcement  
- Clean and structured output  
- Safe handling of missing data  
- Easy to extend for similar documents  

---

## Error Handling
- Extraction failures do not break JSON structure
- Logs can be added for debugging missing or ambiguous fields

---

## Success Criteria
- Each PDF produces a **complete JSON**
- Data is accurate and consistently formatted
- Output can be directly consumed by analytics or business systems without manual correction :contentReference[oaicite:1]{index=1}

---

## Future Enhancements
- Support for additional insurance document types
- Confidence scoring for extracted fields
- Automated validation reports

---

## Author
Developed for scalable and reliable insurance document processing.
Author
[@sonuyadav](https://github.com/raos0nu)
