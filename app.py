from pathlib import Path                  # AUTHOR (@raos0nu)(https://github.com/Raos0nu)

from flask import Flask, render_template_string, request

from ocr_pdf_extract import ocr_pdf

app = Flask(__name__)


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

    if request.method == "POST":
        uploaded = request.files.get("file")
        if not uploaded or uploaded.filename == "":
            error = "Please choose a PDF file to upload."
        else:
            # Save to a local 'uploads' folder to avoid Windows temp-file permission issues
            uploads_dir = Path("uploads")
            uploads_dir.mkdir(exist_ok=True)

            safe_name = Path(uploaded.filename).name or "uploaded.pdf"
            save_path = uploads_dir / safe_name

            try:
                uploaded.save(save_path)
                text = ocr_pdf(save_path)
            except Exception as exc:  # noqa: BLE001
                error = f"Failed to process PDF: {exc}"

    return render_template_string(INDEX_HTML, error=error, text=text)


if __name__ == "__main__":
    # For local development only; use a proper WSGI server for production.
    app.run(debug=True)


