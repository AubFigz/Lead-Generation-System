import os
import shutil

# Define paths and content
NGINX_HTML_PATH = "/usr/share/nginx/html"
STATIC_PATH = "/app/static"

# Error page contents
ERROR_404_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>404 Not Found</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 20%; }
        h1 { font-size: 48px; color: #f00; }
        p { font-size: 24px; }
    </style>
</head>
<body>
    <h1>404 Not Found</h1>
    <p>The page you are looking for does not exist.</p>
</body>
</html>
"""

ERROR_50X_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Server Error</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 20%; }
        h1 { font-size: 48px; color: #f00; }
        p { font-size: 24px; }
    </style>
</head>
<body>
    <h1>Server Error</h1>
    <p>Sorry, something went wrong on our end. Please try again later.</p>
</body>
</html>
"""

# Static file contents
SCRIPT_JS_CONTENT = """
document.addEventListener('DOMContentLoaded', () => {
    console.log("Static JavaScript loaded!");
});
"""

STYLE_CSS_CONTENT = """
body {
    font-family: Arial, sans-serif;
    background-color: #f4f4f9;
    color: #333;
    margin: 0;
    padding: 0;
}
"""

def ensure_directory_exists(path):
    """Ensure a directory exists, creating it if necessary."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def write_file(path, content):
    """Write content to a file."""
    with open(path, "w") as file:
        file.write(content)
        print(f"Written content to: {path}")

def setup_nginx_html():
    """Ensure NGINX HTML directory exists and contains error pages."""
    ensure_directory_exists(NGINX_HTML_PATH)

    # Write error pages
    write_file(os.path.join(NGINX_HTML_PATH, "404.html"), ERROR_404_CONTENT)
    write_file(os.path.join(NGINX_HTML_PATH, "50x.html"), ERROR_50X_CONTENT)

def setup_static_files():
    """Ensure static directory exists and contains static files."""
    ensure_directory_exists(STATIC_PATH)

    # Write static files
    write_file(os.path.join(STATIC_PATH, "script.js"), SCRIPT_JS_CONTENT)
    write_file(os.path.join(STATIC_PATH, "style.css"), STYLE_CSS_CONTENT)

if __name__ == "__main__":
    try:
        print("Setting up NGINX HTML and static directories...")
        setup_nginx_html()
        setup_static_files()
        print("Setup complete.")
    except Exception as e:
        print(f"Error during setup: {e}")
