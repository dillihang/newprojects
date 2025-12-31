import connectviaparamiko
from dateutil import parser
from datetime import datetime
import re
import json
import os
from collections import Counter

# -------------------------
# SSH helper
# -------------------------
def run_command(client: str, command: str):
    out, err, code = connectviaparamiko.run_remote_command(
        client=client,
        command=command
    )
    if code != 0:
        print(f"[ERROR] {err}")
        return None
    return out


# -------------------------
# File search helpers
# -------------------------
def normalize_ext(ext: str):
    return f"*{ext}" if "." in ext else f"*.{ext}"

def build_search_cmd(path: str, ext: str, keyword_list: list | None = None):
    pattern = normalize_ext(ext)

    # Default to your big keyword dictionary
    if not keyword_list:
        keyword_list = list(alert_keywords().keys())

    keywords = "|".join(keyword_list)

    # removed \b as requested
    cmd = f"sudo find {path} -name '{pattern}' -exec grep -i -H -E '({keywords})' {{}} + 2>/dev/null"
    return cmd


# -------------------------
# Severity definitions
# -------------------------
def alert_keywords():
    return {
        "FATAL": 1, "CRITICAL": 1, "PANIC": 1, "EMERGENCY": 1,
        "BREACH": 1, "INTRUSION": 1, "ATTACK": 1, "EXPLOIT": 1,
        "CORRUPTED": 1, "OOMKILLED": 1, "CRASH": 1, "ABORT": 1,

        "ERROR": 2, "FAIL": 2, "SEVERE": 2, "EXCEPTION": 2,
        "DEADLOCK": 2, "VULNERABILITY": 2, "LEAK": 2,
        "OVERFLOW": 2, "EVICTED": 2, "UNHEALTHY": 2,
        "TERMINATED": 2, "SHUTDOWN": 2,

        "WARNING": 3, "ALERT": 3, "TIMEOUT": 3,
        "AUTHENTICATION": 3, "AUTHORIZATION": 3,
        "DENIED": 3, "REFUSED": 3, "BLOCKED": 3,
        "MISSING": 3, "INVALID": 3, "ILLEGAL": 3,

        "UNEXPECTED": 4, "UNHANDLED": 4, "UNCAUGHT": 4,
        "UNSUPPORTED": 4, "DEPRECATED": 4, "HANG": 4,
        "STACKTRACE": 4, "TRACEBACK": 4
    }

def severity_map():
    return {1: "CRITICAL", 2: "HIGH", 3: "MEDIUM", 4: "LOW"}

def get_line_severity_num(line: str, alert_keywords: dict):
    multiple_severity=[]
    for word, severity_num in alert_keywords.items():
        if word.lower() in line.lower():
            multiple_severity.append(severity_num)
    if len(multiple_severity) > 1:
        return min(multiple_severity)
    elif multiple_severity:
        return multiple_severity[0]
    else:
        return None


# -------------------------
# Timestamp extraction
# -------------------------
def check_common_date_patterns(line:str):
    core_timestamp_regex = [
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z', # ISO8601 Z
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}', # ISO8601 offset
        r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', # common
        r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}', # milliseconds
        r'[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}', # syslog
        r'\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}', # Apache/Nginx
    ]
    for pattern in core_timestamp_regex:
        match = re.search(pattern, line)
        if match:
            return match.group(0)
    return None

def common_date_parser(date_str:str):
    try:
        return parser.parse(date_str, fuzzy=True)
    except Exception as e:
        return None

def extract_timestamp(line: str):
    date_match = check_common_date_patterns(line)
    if date_match:
        parsed = common_date_parser(date_match)
        if parsed:
            return parsed
    parsed = common_date_parser(line)
    if parsed:
        return parsed
    return None


# -------------------------
# Log parser (your original one)
# -------------------------
def simple_log_parser(raw_data: list, alert_keywords: dict):
    parsed_data = []

    if not raw_data:
        print("[INFO] No data to parse")
        return parsed_data

    for line in raw_data:
        try:
            timestamp = extract_timestamp(line=line)
            severity_num = get_line_severity_num(line=line, alert_keywords=alert_keywords)
            severity_name = severity_map().get(severity_num, "NONE")
            file_path, log_message = line.split(":", 1)

            parsed_data.append({
                "timestamp": timestamp,
                "severity_num": severity_num,
                "severity": severity_name,
                "file": file_path,
                "message": log_message,
                "raw": line
            })

        except Exception as e:
            print(f"[WARNING] Failed to parse line: {line[:100]}...Error: {e}")

            parsed_data.append({
                "error": str(e),
                "raw": line,
                "severity": "UNKNOWN"
            })

    return parsed_data


# -------------------------
# Aggregator + printer + serializable
# -------------------------
def aggregate_logs(parsed_logs):
    counts = Counter()
    timestamps = []

    for entry in parsed_logs:
        counts[entry["severity"]] += 1
        if entry.get("timestamp"):
            timestamps.append(entry["timestamp"])

    summary = {
        "total_entries": len(parsed_logs),
        "by_severity": dict(counts)
    }

    if timestamps:
        summary["time_range"] = {
            "start": min(timestamps).isoformat(),
            "end": max(timestamps).isoformat()
        }

    return summary

def print_summary(summary):
    print("\n=== LOG SUMMARY ===")
    print(f"Total entries: {summary['total_entries']}\n")
    for sev, count in summary["by_severity"].items():
        print(f"{sev}: {count}")
    if "time_range" in summary:
        print("\nTime range:")
        print(f"From: {summary['time_range']['start']}")
        print(f"To:   {summary['time_range']['end']}")

def make_serializable(parsed_logs):
    serializable = []
    for entry in parsed_logs:
        new_entry = entry.copy()
        if new_entry.get("timestamp"):
            new_entry["timestamp"] = new_entry["timestamp"].isoformat()
        serializable.append(new_entry)
    return serializable

def save_json(summary, parsed_logs, output_dir="/tmp/log_reports"):
    os.makedirs(output_dir, exist_ok=True)
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')

    summary_path = os.path.join(output_dir, f"log_summary_{timestamp_str}.json")
    full_path = os.path.join(output_dir, f"log_full_{timestamp_str}.json")

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=4)
    with open(full_path, "w") as f:
        json.dump(make_serializable(parsed_logs), f, indent=4)

    print(f"\n[INFO] Summary JSON saved to {summary_path}")
    print(f"[INFO] Full parsed JSON saved to {full_path}")


# -------------------------
# Orchestrator
# -------------------------
def orchestrate_log_analysis(client, path, ext, keyword_list=None):
    print("[INFO] Scanning logs remotely...")

    cmd = build_search_cmd(path, ext, keyword_list)
    
    output = run_command(client, cmd)

    if not output:
        print("[INFO] No log matches found.")
        return

    raw_lines = output.splitlines()
    print(f"[INFO] Collected {len(raw_lines)} log lines")

    parsed = simple_log_parser(raw_lines, alert_keywords())

    summary = aggregate_logs(parsed)
    print_summary(summary)
    save_json(summary, parsed)


# -------------------------
# Entry point
# -------------------------
if __name__ == "__main__":
    client = connectviaparamiko.connect_to_server()
    if not client:
        print("errorrrrrrrrr")
    else:
        orchestrate_log_analysis(
            client=client,
            path="/home/",
            ext="log",
            keyword_list=None  # uses your full keyword dictionary
        )
