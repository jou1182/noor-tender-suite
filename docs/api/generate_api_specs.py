import json
import os
import sys

# Ensure application context is within path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi.openapi.utils import get_openapi
from app.main import app

def generate_docs():
    """
    Extracts the native OpenAPI schema from the FastAPI application and compiles 
    it into both a raw JSON specification and an interactive HTML Redoc bundle.
    """
    # Create the output directory relative to this script
    output_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract OpenAPI Schema Dictionary
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description="Noor AI Master Application Programming Interface",
        routes=app.routes,
    )
    
    # 1. Write the raw JSON specification
    json_path = os.path.join(output_dir, 'openapi_specs.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(openapi_schema, f, indent=2)
        
    # 2. Write the interactive Redoc HTML wrapper
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <title>Noor AI - Master API Documentation</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style> body {{ margin: 0; padding: 0; }} </style>
    </head>
    <body>
    <redoc spec-url='./openapi_specs.json'></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"> </script>
    </body>
    </html>
    """
    
    html_path = os.path.join(output_dir, 'index.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"[SUCCESS] API OpenAPI Schema compiled to: {json_path}")
    print(f"[SUCCESS] Interactive HTML Docs generated to: {html_path}")

if __name__ == "__main__":
    print("Extracting Route Endpoints and Compiling Schema...")
    generate_docs()
