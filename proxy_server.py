from flask import Flask, request, Response, send_from_directory
import logging
import requests
import os

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# Define static directory
STATIC_DIR = "static"
os.makedirs(STATIC_DIR, exist_ok=True)

@app.route('/proxy', methods=['GET'])
def proxy():
    """
    Proxies a request to the Credential Finder pathway display and injects custom CSS.
    
    Retrieves the HTML content for a specified pathway ID, injects custom CSS and a debug script into the HTML head,
    and rewrites asset paths to ensure they are served through this proxy.

    Args:
        id (str): The ID of the pathway to fetch, specified as a query parameter.

    Returns:
        Response: A Flask response object containing the modified HTML content or an error message with corresponding status code.
    """
    base_url = "https://credentialfinder.org/pathwaydisplay/"
    pathway_id = request.args.get('id', '')

    if not pathway_id:
        return "Error: No ID provided", 400

    target_url = f"{base_url}?id={pathway_id}"
    response = requests.get(target_url)

    if response.status_code != 200:
        return f"Error fetching content: {response.status_code}", response.status_code

    # Inject custom CSS and debug script
    custom_css_link = '<link rel="stylesheet" href="/static/customTest.css">'
    debug_script = """
    <script>
        console.log("Custom CSS file has been injected.");
        document.body.style.border = "5px solid red"; // Debugging
    </script>
    """
    html_content = response.text.replace("</head>", f"{custom_css_link}{debug_script}</head>")


    # Replace SVG and asset paths to use the proxy route
    html_content = html_content.replace(
        'https://credentialfinder.org/pathwaydisplay/',
        '/proxy/'  # Proxy through your server
    )


    app.logger.debug("Modified HTML with injected custom.css and debug script.")
    return Response(html_content, content_type="text/html")

@app.route('/proxy/<path:filename>')
def proxy_static_files(filename):
    """
    Serve static files like SVGs and PNGs by proxying to the remote server or serving locally if available.
    """
    remote_base_url = "https://credentialfinder.org/pathwaydisplay/"
    local_path = os.path.join(STATIC_DIR, filename)

    app.logger.debug(f"Attempting to serve/proxy file: {filename}")

    # Serve file locally if it exists
    if os.path.exists(local_path):
        app.logger.debug(f"Serving local file: {local_path}")
        return send_from_directory(STATIC_DIR, filename)

    # Proxy request to the remote server
    remote_url = f"{remote_base_url}{filename}"
    app.logger.debug(f"File not found locally. Proxying from remote: {remote_url}")
    response = requests.get(remote_url)

    if response.status_code == 200:
        app.logger.debug(f"Proxying file from remote: {remote_url}")
        content_type = response.headers.get("Content-Type", "image/svg+xml")
        return Response(response.content, content_type=content_type)
    else:
        app.logger.error(f"Failed to fetch {filename} from remote. Status: {response.status_code}")
        return f"File not found: {filename}", 404

@app.route('/<path:filename>')
def serve_or_proxy_file(filename):
    """
    Handle requests for top-level file paths.
    """
    app.logger.debug(f"Handling request for: {filename}")
    

    # Check if the file exists in the local static directory
    local_path = os.path.join(STATIC_DIR, filename)
    if os.path.exists(local_path):
        app.logger.debug(f"Serving local file: {local_path}")
        return send_from_directory(STATIC_DIR, filename)

    # Otherwise, proxy the request to the remote server
    remote_base_url = "https://credentialfinder.org/pathwaydisplay/"
    remote_url = f"{remote_base_url}{filename}"
    app.logger.debug(f"Proxying file from remote: {remote_url}")
    response = requests.get(remote_url)

    if response.status_code == 200:
        app.logger.debug(f"Successfully fetched remote file: {remote_url}")
        content_type = response.headers.get("Content-Type", "image/svg+xml")
        return Response(response.content, content_type=content_type)
    else:
        app.logger.error(f"Failed to fetch {filename} from remote. Status: {response.status_code}")
        return f"File not found: {filename}", 404


@app.route('/static/<path:filename>')
def static_files(filename):
    app.logger.debug(f"Serving static file: {filename}")
    return send_from_directory(STATIC_DIR, filename)

@app.route('/bundle.js')
def serve_bundle_js():
    js_url = "https://credentialfinder.org/pathwaydisplay/bundle.js"
    js_response = requests.get(js_url)

    if js_response.status_code == 200:
        app.logger.debug("Serving bundle.js from remote URL.")
        return Response(js_response.content, content_type='application/javascript')

    app.logger.warning("bundle.js not found.")
    return "File not found", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
