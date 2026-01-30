import os
import ast
import re
import xml.etree.ElementTree as ET


def valid_ros_name(name):
    if not isinstance(name, str):
        return False
    return bool(re.match(r'^(/[a-z0-9_]+)+$', name))


class ROSProjectAnalyzer:
    def __init__(self, root_dir):
        self.root_dir = root_dir

        self.nodes = set()
        self.topics = set()

        self.publishers = []
        self.subscribers = []

        self.rate_usage = []
        self.init_shutdown = []
        self.naming_issues = []

    # --------------------------------------------------
    # Main entry point
    
    def analyze(self):
        for root, _, files in os.walk(self.root_dir):
            for name in files:
                path = os.path.join(root, name)

                if name.endswith(".py"):
                    self.analyze_python(path)
                elif name.endswith((".cpp", ".cc", ".h", ".hpp")):
                    self.analyze_cpp(path)
                elif name.endswith(".launch"):
                    self.analyze_launch_xml(path)
                elif name.endswith(".launch.py"):
                    self.analyze_launch_py(path)

        return self.summary()

    # --------------------------------------------------
    # Python ROS analysis
    
    def analyze_python(self, path):
        try:
            tree = ast.parse(open(path, "r", encoding="utf-8", errors="ignore").read())
        except Exception:
            return

        for node in ast.walk(tree):

            # Detect while loops without rospy.Rate
            if isinstance(node, ast.While):
                has_rate = any(
                    isinstance(child, ast.Call)
                    and hasattr(child.func, "attr")
                    and child.func.attr == "Rate"
                    for child in ast.walk(node)
                )
                if not has_rate:
                    self.rate_usage.append((path, "while loop WITHOUT rospy.Rate"))

            if not isinstance(node, ast.Call):
                continue
            if not hasattr(node.func, "attr"):
                continue

            name = node.func.attr

            # Init / shutdown
            if name == "init_node":
                self.nodes.add(path)
                self.init_shutdown.append((path, "rospy.init_node"))

            if name == "is_shutdown":
                self.init_shutdown.append((path, "rospy.is_shutdown"))

            # Rate
            if name == "Rate":
                self.rate_usage.append((path, "rospy.Rate"))

            # ROS1 Pub/Sub
            if name in ("Publisher", "Subscriber"):
                topic = self.get_arg(node, 0)
                if name == "Publisher":
                    self.publishers.append((path, topic))
                else:
                    self.subscribers.append((path, topic))

                self.topics.add(topic)
                if not valid_ros_name(topic):
                    self.naming_issues.append((path, topic))

            # ROS2 Pub/Sub
            if name in ("create_publisher", "create_subscription"):
                self.nodes.add(path)
                topic = self.get_arg(node, 1)

                if name == "create_publisher":
                    self.publishers.append((path, topic))
                else:
                    self.subscribers.append((path, topic))

                self.topics.add(topic)
                if not valid_ros_name(topic):
                    self.naming_issues.append((path, topic))

    def get_arg(self, node, index):
        try:
            arg = node.args[index]
            if isinstance(arg, ast.Constant):
                return arg.value
        except Exception:
            pass
        return "unknown"

    # --------------------------------------------------
    # C++ ROS analysis
 
    def analyze_cpp(self, path):
        try:
            text = open(path, "r", errors="ignore").read()
        except Exception:
            return

        # Init / shutdown
        if "ros::init" in text:
            self.init_shutdown.append((path, "ros::init"))

        if "ros::shutdown" in text or "ros::ok" in text:
            self.init_shutdown.append((path, "ros shutdown handling"))

        # Rate
        if "ros::Rate" in text:
            self.rate_usage.append((path, "ros::Rate"))

        if re.search(r'while\s*\(\s*ros::ok\s*\(\s*\)\s*\)', text) and "ros::Rate" not in text:
            self.rate_usage.append((path, "while(ros::ok()) WITHOUT ros::Rate"))

        # Publishers
        for topic in re.findall(r'advertise<.*?>\("(.+?)"', text):
            self.publishers.append((path, topic))
            self.topics.add(topic)
            if not valid_ros_name(topic):
                self.naming_issues.append((path, topic))

        # Subscribers
        for topic in re.findall(r'subscribe<.*?>\("(.+?)"', text):
            self.subscribers.append((path, topic))
            self.topics.add(topic)
            if not valid_ros_name(topic):
                self.naming_issues.append((path, topic))

    # --------------------------------------------------
    # Launch files
    
    def analyze_launch_xml(self, path):
        try:
            root = ET.parse(path).getroot()
        except Exception:
            return

        for node in root.findall("node"):
            pkg = node.attrib.get("pkg", "")
            name = node.attrib.get("name", "unknown")
            self.nodes.add(f"{pkg}/{name}")

    def analyze_launch_py(self, path):
        try:
            text = open(path, "r", errors="ignore").read()
        except Exception:
            return

        if "Node(" in text:
            self.nodes.add(path)

    # --------------------------------------------------
    # Summary & metrics
   
    def summary(self):
        return {
            "metrics": {
                "Nodes detected": len(self.nodes),
                "Topics detected": len(self.topics),
                "Publishers": len(self.publishers),
                "Subscribers": len(self.subscribers),
                "Rate-controlled loops": len(self.rate_usage),
                "Naming violations": len(self.naming_issues),
            },
            "publishers": self.publishers,
            "subscribers": self.subscribers,
            "rate_analysis": self.rate_usage,
            "init_shutdown": self.init_shutdown,
            "naming_issues": self.naming_issues,
        }

    # --------------------------------------------------
    # Behavior explanation
   
    def explain_behavior(self, summary):
        lines = []
        lines.append("Robot Behavior Explanation")
        lines.append("=" * 35)
        lines.append(f"Detected {summary['metrics']['Nodes detected']} ROS nodes.")
        lines.append(f"Detected {summary['metrics']['Topics detected']} topics.\n")

        if summary["rate_analysis"]:
            lines.append("Timing & Execution:")
            for r in summary["rate_analysis"]:
                lines.append(f" - {r[0]} → {r[1]}")
            lines.append("")
        else:
            lines.append("No rate-controlled execution detected.\n")

        if summary["naming_issues"]:
            lines.append("Naming Convention Issues:")
            for n in summary["naming_issues"]:
                lines.append(f" - {n[0]} → invalid topic name: {n[1]}")
            lines.append("")
        else:
            lines.append("All topics follow ROS naming conventions.\n")

        lines.append("Communication Model:")
        for p in summary["publishers"]:
            lines.append(f" - {p[0]} publishes on {p[1]}")
        for s in summary["subscribers"]:
            lines.append(f" - {s[0]} subscribes to {s[1]}")

        return "\n".join(lines)
