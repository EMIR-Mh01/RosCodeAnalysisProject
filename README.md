# RosCodeAnalysisProject
# RosCodeAnalysisProject
[![Python](https://img.shields.io/badge/Python-3.10-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
A web-based Python tool to analyze ROS1/ROS2 projects. Detect nodes, topics, publishers/subscribers, rate-controlled loops, and naming convention issues.
1. Architecture

The system is structured as a Python Flask web application with a modular analyzer.

flowchart TD
    A[Flask App<br>(Web UI + Routes)] --> B[ROSProjectAnalyzer<br>- Python code parsing<br>- C++ code parsing<br>- Launch file parsing<br>- Metrics & summary]
    B --> C[Output & Visualization<br>- Metrics<br>- Behavior explanation<br>- Save results]


Explanation:

Flask App – Handles user uploads, routing, and displaying results in the browser.

ROSProjectAnalyzer – Core logic to parse Python, C++, and launch files, extract metrics, and detect ROS issues.

Output & Visualization – Displays metrics and behavior explanations, with option to save results as a text file.

2. Design Decisions

Flask Web Interface: Simple and lightweight GUI for uploading ROS projects and viewing results.

Modular Analyzer: ROSProjectAnalyzer class separates code parsing from web handling for maintainability.

Python AST Module: Reliable way to detect ROS calls like rospy.init_node, Publisher, Subscriber, and loop structures.

Regex for C++ Parsing: Efficient method to extract advertise, subscribe, and ros::Rate usage.

XML Parsing for Launch Files: Detects nodes defined in .launch files accurately.

Validation & Metrics: Checks for rate-controlled loops, proper ROS topic names, and naming violations.

Save/Reload Feature: Users can save results in a text file for documentation or later reference.

3. Setup and Execution Instructions
Requirements

Python 3.10+

Flask (pip install flask)

Steps

Clone the repository:

git clone <repo_url>
cd RosCodeAnalysisProject


Install dependencies:

pip install flask


Run the Flask app:

python app.py


Open your browser:

http://127.0.0.1:5000


Upload a ROS project folder or ZIP file.

View metrics, behavior explanation, and optionally save the analysis.

4. Supported File Types

Python: .py

C++: .cpp, .hpp, .h

ROS Launch: .launch, .launch.py

ZIP archives containing a ROS project

5. Features

🚀 Detect ROS nodes (Python, C++, launch files)

📡 Identify publishers and subscribers

⏱ Analyze rate-controlled loops (Rate)

🔤 Check ROS topic naming conventions

📝 Generate concise behavior summaries

💾 Save results for later use

6. Output

The analyzer generates:

Metrics summary: nodes, topics, publishers, subscribers

Rate-controlled loop usage

Naming convention violations

High-level behavior explanation

Option to download a .txt file with results
