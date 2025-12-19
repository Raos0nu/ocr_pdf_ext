from pathlib import Path                  # AUTHOR (@raos0nu)(https://github.com/Raos0nu)
import os
import json

from flask import Flask, render_template_string, request, jsonify

from ocr_pdf_extract import ocr_pdf
from field_extractor import extract_insurance_fields

app = Flask(__name__)


INDEX_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Motor Insurance PDF Data Extraction</title>
    <style>
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      
      body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        padding: 20px;
        color: #333;
      }
      
      .container {
        max-width: 1200px;
        margin: 0 auto;
      }
      
      .header {
        text-align: center;
        color: white;
        margin-bottom: 30px;
      }
      
      .header h1 {
        font-size: 2.5rem;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
      }
      
      .header p {
        font-size: 1.1rem;
        opacity: 0.9;
      }
      
      .card {
        background: white;
        border-radius: 16px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        padding: 30px;
        margin-bottom: 20px;
      }
      
      .upload-section {
        text-align: center;
      }
      
      .upload-section h2 {
        color: #667eea;
        margin-bottom: 20px;
        font-size: 1.5rem;
      }
      
      .file-input-wrapper {
        position: relative;
        display: inline-block;
        margin: 20px 0;
      }
      
      .file-input-wrapper input[type="file"] {
        position: absolute;
        opacity: 0;
        width: 100%;
        height: 100%;
        cursor: pointer;
      }
      
      .file-input-label {
        display: inline-block;
        padding: 12px 24px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        transition: transform 0.2s, box-shadow 0.2s;
      }
      
      .file-input-label:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
      }
      
      .file-name {
        margin-top: 10px;
        color: #666;
        font-size: 0.9rem;
      }
      
      .submit-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 14px 32px;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        margin-top: 15px;
      }
      
      .submit-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
      }
      
      .submit-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
        transform: none;
      }
      
      .error {
        background: #fee;
        color: #c33;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0;
        border-left: 4px solid #c33;
      }
      
      .success {
        background: #efe;
        color: #3c3;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0;
        border-left: 4px solid #3c3;
      }
      
      .results-section {
        display: none;
      }
      
      .results-section.active {
        display: block;
      }
      
      .results-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        flex-wrap: wrap;
        gap: 10px;
      }
      
      .results-header h2 {
        color: #667eea;
        font-size: 1.8rem;
      }
      
      .json-toggle {
        background: #667eea;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.9rem;
      }
      
      .json-toggle:hover {
        background: #5568d3;
      }
      
      .fields-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 15px;
        margin-bottom: 20px;
      }
      
      .field-card {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        transition: transform 0.2s, box-shadow 0.2s;
      }
      
      .field-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      }
      
      .field-label {
        font-size: 0.85rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        font-weight: 600;
      }
      
      .field-value {
        font-size: 1rem;
        color: #333;
        word-break: break-word;
      }
      
      .field-value.empty {
        color: #999;
        font-style: italic;
      }
      
      .json-view {
        display: none;
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 20px;
        border-radius: 8px;
        overflow-x: auto;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        line-height: 1.6;
        max-height: 600px;
        overflow-y: auto;
      }
      
      .json-view.active {
        display: block;
      }
      
      .json-view pre {
        margin: 0;
        white-space: pre-wrap;
        word-wrap: break-word;
      }
      
      .stats {
        display: flex;
        gap: 20px;
        margin-bottom: 20px;
        flex-wrap: wrap;
      }
      
      .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        flex: 1;
        min-width: 150px;
      }
      
      .stat-label {
        font-size: 0.85rem;
        opacity: 0.9;
        margin-bottom: 5px;
      }
      
      .stat-value {
        font-size: 1.5rem;
        font-weight: bold;
      }
      
      .loading {
        display: none;
        text-align: center;
        padding: 20px;
      }
      
      .loading.active {
        display: block;
      }
      
      .spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 0 auto 10px;
      }
      
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
      
      @media (max-width: 768px) {
        .header h1 {
          font-size: 2rem;
        }
        
        .fields-grid {
          grid-template-columns: 1fr;
        }
        
        .card {
          padding: 20px;
        }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="header">
        <h1>🏍️ Motor Insurance PDF Data Extraction</h1>
        <p>Extract structured data from insurance policy documents</p>
      </div>
      
      <div class="card upload-section">
        <h2>Upload Policy PDF</h2>
        <form method="post" enctype="multipart/form-data" id="uploadForm">
          <div class="file-input-wrapper">
            <input type="file" id="file" name="file" accept="application/pdf" required />
            <label for="file" class="file-input-label">📄 Choose PDF File</label>
          </div>
          <div class="file-name" id="fileName"></div>
          <button type="submit" class="submit-btn" id="submitBtn">Extract Data</button>
        </form>
        
        <div class="loading" id="loading">
          <div class="spinner"></div>
          <p>Processing PDF... This may take a moment.</p>
        </div>
        
        {% if error %}
          <div class="error">{{ error }}</div>
        {% endif %}
        
        {% if success %}
          <div class="success">{{ success }}</div>
        {% endif %}
      </div>
      
      {% if extracted_data %}
      <div class="card results-section active" id="resultsSection">
        <div class="results-header">
          <h2>📊 Extracted Data</h2>
          <button type="button" class="json-toggle" onclick="toggleJsonView()">View JSON</button>
        </div>
        
        <div class="stats">
          <div class="stat-card">
            <div class="stat-label">Fields Extracted</div>
            <div class="stat-value">{{ field_count }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Fields with Data</div>
            <div class="stat-value">{{ filled_count }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Completion Rate</div>
            <div class="stat-value">{{ completion_rate }}%</div>
          </div>
        </div>
        
        <div class="fields-grid" id="fieldsView">
          {% for key, value in extracted_data.items() %}
          <div class="field-card">
            <div class="field-label">{{ key }}</div>
            <div class="field-value {% if not value %}empty{% endif %}">
              {{ value if value else "(Not found)" }}
            </div>
          </div>
          {% endfor %}
        </div>
        
        <div class="json-view" id="jsonView">
          <pre>{{ json_data }}</pre>
        </div>
      </div>
      {% endif %}
    </div>
    
    <script>
      // File name display
      document.getElementById('file').addEventListener('change', function(e) {
        const fileName = e.target.files[0]?.name || '';
        document.getElementById('fileName').textContent = fileName ? `Selected: ${fileName}` : '';
      });
      
      // Form submission loading
      document.getElementById('uploadForm').addEventListener('submit', function() {
        document.getElementById('loading').classList.add('active');
        document.getElementById('submitBtn').disabled = true;
      });
      
      // JSON view toggle
      function toggleJsonView() {
        const fieldsView = document.getElementById('fieldsView');
        const jsonView = document.getElementById('jsonView');
        const toggleBtn = document.querySelector('.json-toggle');
        
        if (jsonView.classList.contains('active')) {
          jsonView.classList.remove('active');
          fieldsView.style.display = 'grid';
          toggleBtn.textContent = 'View JSON';
        } else {
          jsonView.classList.add('active');
          fieldsView.style.display = 'none';
          toggleBtn.textContent = 'View Fields';
        }
      }
    </script>
  </body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    error = ""
    success = ""
    extracted_data = None
    json_data = ""
    field_count = 0
    filled_count = 0
    completion_rate = 0

    if request.method == "POST":
        uploaded = request.files.get("file")
        if not uploaded or uploaded.filename == "":
            error = "Please choose a PDF file to upload."
        else:
            # On Vercel, the filesystem is read-only except for /tmp, so we use it there.
            # Locally, we keep using a relative 'uploads' folder for convenience.
            if os.environ.get("VERCEL_ENV"):
                uploads_dir = Path("/tmp/uploads")
            else:
                uploads_dir = Path("uploads")

            uploads_dir.mkdir(parents=True, exist_ok=True)

            safe_name = Path(uploaded.filename).name or "uploaded.pdf"
            save_path = uploads_dir / safe_name

            try:
                uploaded.save(save_path)
                
                # Extract text from PDF
                text = ocr_pdf(save_path)
                
                # Extract structured fields
                extracted_data = extract_insurance_fields(text)
                
                # Calculate statistics
                field_count = len(extracted_data)
                filled_count = sum(1 for v in extracted_data.values() if v and v.strip())
                completion_rate = round((filled_count / field_count * 100) if field_count > 0 else 0, 1)
                
                # Format JSON for display
                json_data = json.dumps(extracted_data, indent=2, ensure_ascii=False)
                
                success = f"Successfully extracted data from PDF! Found {filled_count} out of {field_count} fields."
                
                # Clean up uploaded file
                try:
                    save_path.unlink()
                except Exception:
                    pass  # Ignore cleanup errors
                    
            except Exception as exc:  # noqa: BLE001
                error = f"Failed to process PDF: {str(exc)}"

    return render_template_string(
        INDEX_HTML,
        error=error,
        success=success,
        extracted_data=extracted_data,
        json_data=json_data,
        field_count=field_count,
        filled_count=filled_count,
        completion_rate=completion_rate,
    )


@app.route("/api/extract", methods=["POST"])
def api_extract():
    """API endpoint for programmatic access"""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    uploaded = request.files["file"]
    if uploaded.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    
    try:
        # Save file
        if os.environ.get("VERCEL_ENV"):
            uploads_dir = Path("/tmp/uploads")
        else:
            uploads_dir = Path("uploads")
        
        uploads_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(uploaded.filename).name or "uploaded.pdf"
        save_path = uploads_dir / safe_name
        uploaded.save(save_path)
        
        # Extract text and fields
        text = ocr_pdf(save_path)
        extracted_data = extract_insurance_fields(text)
        
        # Clean up
        try:
            save_path.unlink()
        except Exception:
            pass
        
        return jsonify(extracted_data), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # For local development only; use a proper WSGI server for production.
    app.run(debug=True)
