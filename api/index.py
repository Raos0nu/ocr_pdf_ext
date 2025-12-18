from pathlib import Path
import tempfile
import os
import traceback

from flask import Flask, render_template_string, request

# Import OCR function with error handling
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ocr_pdf_extract import ocr_pdf
    OCR_AVAILABLE = True
except Exception as e:  # noqa: BLE001
    OCR_AVAILABLE = False
    OCR_ERROR = str(e)
    print(f"Warning: OCR module failed to import: {e}")
    print(traceback.format_exc())

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


INDEX_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Motor Insurance PDF OCR</title>
    <style>
      body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 24px; }
      h1 { font-size: 24px; margin-bottom: 16px; }
      form { margin-bottom: 24px; padding: 16px; border: 1px solid #ddd; border-radius: 8px; max-width: 480px; }
      input[type="file"] { margin: 8px 0 16px 0; }
      button { background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
      button:hover { background: #1d4ed8; }
      .result { white-space: pre-wrap; border: 1px solid #eee; padding: 12px; border-radius: 6px; max-height: 480px; overflow: auto; background: #fafafa; }
      .error { color: #b91c1c; margin-bottom: 12px; }
    </style>
  </head>
  <body>
    <h1>Motor Insurance PDF OCR</h1>
    <form method="post" enctype="multipart/form-data">
      <label for="file">Upload policy PDF:</label><br />
      <input id="file" name="file" type="file" accept="application/pdf" required />
      <br />
      <button type="submit">Extract Text</button>
    </form>

    {% if error %}
      <div class="error">{{ error }}</div>
    {% endif %}

    {% if text %}
      <h2>Extracted Text</h2>
      <div class="result">{{ text }}</div>
    {% endif %}
  </body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    error = ""
    text = ""

    # Check if OCR is available
    if not OCR_AVAILABLE:
        error = f"OCR module not available. Error: {OCR_ERROR}. This usually means Tesseract OCR is not installed on the server."
        return render_template_string(INDEX_HTML, error=error, text=text)

    if request.method == "POST":
        uploaded = request.files.get("file")
        if not uploaded or uploaded.filename == "":
            error = "Please choose a PDF file to upload."
        else:
            # Use /tmp directory for Vercel (writable in serverless environment)
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir="/tmp") as tmp:
                    tmp_path = tmp.name
                    uploaded.save(tmp_path)
                
                # Process PDF
                text = ocr_pdf(Path(tmp_path))
                
            except Exception as exc:  # noqa: BLE001
                error = f"Failed to process PDF: {exc}"
                # Include traceback for debugging
                error += f"\n\nTraceback:\n{traceback.format_exc()}"
            finally:
                # Clean up temp file
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except:  # noqa: BLE001, S110
                        pass

    return render_template_string(INDEX_HTML, error=error, text=text)


# Vercel Python runtime handler
# Vercel automatically detects Flask apps in api/ directory
# The app variable is the WSGI application that Vercel will use

