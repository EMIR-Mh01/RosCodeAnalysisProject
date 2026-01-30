import sys
import os
import zipfile
import shutil
from flask import Flask, request, redirect, url_for

# Fix import path to include analyzer module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyzer.ros_project_analyzer import ROSProjectAnalyzer

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# Global storage for last analysis
LAST_RESULT = None
LAST_EXPLANATION = None


@app.route("/", methods=["GET", "POST"])
def index():
    global LAST_RESULT, LAST_EXPLANATION

    if request.method == "POST":
        uploaded_file = request.files.get("ros_file")

        if not uploaded_file or uploaded_file.filename == "":
            return "<h3>No file selected</h3>"

        filename = uploaded_file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        uploaded_file.save(filepath)

        extract_dir = os.path.join(UPLOAD_FOLDER, os.path.splitext(filename)[0])
        os.makedirs(extract_dir, exist_ok=True)

        if filename.endswith(".zip"):
            if not zipfile.is_zipfile(filepath):
                return "<h3>Error: Invalid ZIP file</h3>"
            with zipfile.ZipFile(filepath, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
        else:
            shutil.copy(filepath, extract_dir)

        analyzer = ROSProjectAnalyzer(extract_dir)
        LAST_RESULT = analyzer.analyze()
        LAST_EXPLANATION = analyzer.explain_behavior(LAST_RESULT)

        return render_result()

    return upload_form()


@app.route("/save", methods=["POST"])
def save():
    if LAST_RESULT is None:
        return "<h3>No analysis to save</h3>"

    output_path = os.path.join(RESULT_FOLDER, "analysis_result.txt")

    with open(output_path, "w") as f:
        f.write("ROS ANALYSIS RESULTS\n")
        f.write("=" * 40 + "\n\n")
        f.write(str(LAST_RESULT))
        f.write("\n\n")
        f.write(LAST_EXPLANATION)

    return f"""
    <h3>Results saved successfully</h3>
    <p>File: {output_path}</p>
    <a href="/">Back</a>
    """


@app.route("/new", methods=["POST"])
def new_analysis():
    global LAST_RESULT, LAST_EXPLANATION

    LAST_RESULT = None
    LAST_EXPLANATION = None

    shutil.rmtree(UPLOAD_FOLDER, ignore_errors=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    return redirect(url_for("index"))


def upload_form():
    return """
    <html>
    <head>
        <title>ROS Project Analyzer</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f6f8;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }

            .container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                width: 500px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                text-align: center;
            }

            h1 {
                color: #1f4ed8;
                margin-bottom: 10px;
            }

            p {
                color: #475569;
                margin-bottom: 25px;
            }

            input[type="file"] {
                margin: 20px 0;
                font-size: 14px;
            }

            button {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 12px 20px;
                font-size: 15px;
                border-radius: 6px;
                cursor: pointer;
                width: 100%;
            }

            button:hover {
                background-color: #1e40af;
            }

            .note {
                margin-top: 20px;
                font-size: 12px;
                color: #64748b;
            }
        </style>
    </head>

    <body>
        <div class="container">
            <h1>ROS Project Analyzer</h1>
            <p>
                Upload a ROS project folder or ZIP file to analyze nodes,
                topics, execution timing, and best-practice compliance.
            </p>

            <form method="post" enctype="multipart/form-data">
                <input type="file" name="ros_file" required>
                <button type="submit">Analyze Project</button>
            </form>

            <div class="note">
                Supported formats: <b>.zip</b>, <b>.py</b>, <b>.cpp</b>, <b>.hpp</b>
            </div>
        </div>
    </body>
    </html>
    """



def render_result():
    metrics = LAST_RESULT["metrics"]

    def metric_row(name, value):
        color = "ok"
        if "violations" in name.lower() and value > 0:
            color = "bad"
        return f"""
        <tr>
            <td>{name}</td>
            <td class="{color}">{value}</td>
        </tr>
        """

    metrics_html = "".join(
        metric_row(k, v) for k, v in metrics.items()
    )

    return f"""
    <html>
    <head>
        <title>ROS Project Analysis</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f6f8;
                padding: 30px;
            }}

            h1 {{
                color: #1f4ed8;
                border-bottom: 3px solid #1f4ed8;
                padding-bottom: 10px;
            }}

            h2 {{
                color: #2563eb;
            }}

            table {{
                border-collapse: collapse;
                width: 60%;
                margin-bottom: 30px;
                background: white;
            }}

            th, td {{
                border: 1px solid #ddd;
                padding: 10px;
                text-align: left;
            }}

            th {{
                background-color: #e5e7eb;
            }}

            .ok {{
                color: #15803d;
                font-weight: bold;
            }}

            .bad {{
                color: #b91c1c;
                font-weight: bold;
            }}

            .warning {{
                color: #b45309;
                font-weight: bold;
            }}

            pre {{
                background: #0f172a;
                color: #e5e7eb;
                padding: 15px;
                border-radius: 6px;
                overflow-x: auto;
            }}

            button {{
                padding: 10px 16px;
                font-size: 14px;
                margin-right: 10px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }}

            .save {{
                background-color: #16a34a;
                color: white;
            }}

            .new {{
                background-color: #2563eb;
                color: white;
            }}
        </style>
    </head>

    <body>
        <h1>ROS Project Analysis Report</h1>

        <h2>📊 Metrics Summary</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            {metrics_html}
        </table>

        <h2>🧠 Behavior Explanation</h2>
        <pre>{LAST_EXPLANATION}</pre>

        <form method="post" action="/save">
            <button class="save" type="submit">Save Results</button>
        </form>

        <form method="post" action="/new">
            <button class="new" type="submit">New Analysis</button>
        </form>
    </body>
    </html>
    """



if __name__ == "__main__":
    app.run(debug=True)
