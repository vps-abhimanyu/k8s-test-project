from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route("/")
def index():
    # Read API base URL from environment variables
    api_base = os.getenv("API_BASE", "http://localhost:8000")
    return render_template("index.html", api_base=api_base)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
