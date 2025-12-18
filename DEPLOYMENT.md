# Vercel Deployment Guide

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI** (optional, for CLI deployment):
   ```bash
   npm i -g vercel
   ```

## Important: Tesseract OCR Installation

⚠️ **Vercel's serverless environment does NOT include Tesseract OCR by default.**

You have two options:

### Option 1: Use Vercel Build Command (Recommended)

Add a build command to install Tesseract. Update `vercel.json`:

```json
{
  "buildCommand": "apt-get update && apt-get install -y tesseract-ocr"
}
```

However, Vercel's build environment may not allow `apt-get`. In that case, use Option 2.

### Option 2: Use Tesseract Binary in Project

1. Download Tesseract binary for Linux
2. Include it in your project
3. Update `ocr_pdf_extract.py` to point to the binary path

### Option 3: Use Cloud OCR API (Alternative)

Consider using a cloud OCR service like:
- Google Cloud Vision API
- AWS Textract
- Azure Computer Vision

This avoids the Tesseract installation issue entirely.

## Deployment Steps

### Method 1: Vercel Dashboard

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click "Add New Project"
3. Import your Git repository (GitHub/GitLab/Bitbucket)
4. Vercel will auto-detect Python
5. Build settings:
   - **Framework Preset**: Other
   - **Root Directory**: `./`
   - **Build Command**: (leave empty or add Tesseract install)
   - **Output Directory**: (leave empty)
6. Click "Deploy"

### Method 2: Vercel CLI

```bash
# Install Vercel CLI (if not installed)
npm i -g vercel

# Login to Vercel
vercel login

# Deploy
cd "d:\Motor Insurance PDF Data Extraction"
vercel

# For production deployment
vercel --prod
```

## File Structure

Your project should have:
```
.
├── api/
│   └── index.py          # Vercel serverless function handler
├── ocr_pdf_extract.py    # OCR logic
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel configuration
└── .vercelignore        # Files to exclude from deployment
```

## Environment Variables

If you need any API keys or configuration, add them in:
- Vercel Dashboard → Project → Settings → Environment Variables

## Testing Locally

Test the Vercel setup locally:

```bash
# Install Vercel CLI
npm i -g vercel

# Run local dev server
vercel dev
```

## Troubleshooting

### Tesseract Not Found Error

If you see `TesseractNotFoundError`:
1. Check if Tesseract is installed in the build environment
2. Consider using Option 3 (Cloud OCR API) instead
3. Or use a Docker-based deployment (Vercel doesn't support Docker, consider Railway/Render instead)

### Function Timeout

If OCR takes too long:
- Vercel free tier has a 10-second timeout
- Pro tier allows up to 60 seconds (configured in `vercel.json`)
- For longer processing, consider:
  - Using a queue system (e.g., Vercel Queue)
  - Processing in background jobs
  - Using faster OCR settings (lower DPI)

### File Size Limits

- Vercel has a 4.5MB request body limit on free tier
- Increase in `vercel.json` if needed (Pro tier allows larger)

## Alternative Deployment Options

If Tesseract installation is problematic on Vercel, consider:

1. **Railway**: Supports Docker, easier to install system packages
2. **Render**: Similar to Railway, good Python support
3. **Fly.io**: Full control over environment
4. **AWS Lambda**: With Lambda Layers for Tesseract

