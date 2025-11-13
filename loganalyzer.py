"""
Log Analyzer

This module provides tools to read, analyze, visualize, and report server log data.

Features:
---------
1. Log Reading & Storage:
   - Reads `.log` files from a specified folder.
   - Filters logs based on optional start and end dates.
   - Stores logs in a structured dictionary by date, time, and event type.

2. Log Searching:
   - Search logs by date, time, event type (INFO, WARNING, ERROR), or keywords.
   - Flexible filtering to inspect specific events.

3. Statistics & Insights:
   - Compute total counts of INFO, WARNING, and ERROR events per day or for a date range.
   - Identify most frequent errors and top 3 warning keywords.
   - Generate alerts for high-frequency events (ERROR ≥5, WARNING ≥10).

4. Reporting & Persistence:
   - Generate textual reports with statistical summaries and insights.
   - Save analysis results to JSON files for persistence.
   - Optionally generate daily or trend reports.

5. Visualization:
   - Bar charts for daily event counts (INFO, WARNING, ERROR).
   - Line charts showing trends in errors and warnings over time.
   - Saves visualizations as PNG files in a reports directory.

Usage:
------
1. Initialize empty log structures:
   lines_list = []
   log_dict = {}

2. Read logs:
   read_log_file(folder_path, start_date=start, end_date=end)

3. Generate insights:
   print_statistical_summary_insights(focus_date=some_date)
   generate_report(focus_date=some_date)
   save_json(provided_date=some_date)

4. Visualize logs:
   data_visualizer(provided_date=some_date)

Note:
-----
- The `provided_date` parameter allows focusing analysis and visualization on a specific day.
- For trend line visualizations, all loaded logs are considered.
- Email alert functionality is currently optional and not implemented.

Author: Dillihang Limbu
Date: 13/11/2025
"""
from datetime import datetime, timedelta, date, time
from collections import Counter
from contextlib import redirect_stdout
import os
import json
import glob
import matplotlib.pyplot as plt

def read_log_file(folder_path: str, start_date: date = None, end_date: date = None):
    for file_path in glob.glob(f"{folder_path}/*.log"):
        with open(file_path, "r") as log_file:
            for line in log_file:
                line = line.strip()
                if not line:
                    continue

                lines_list.append(line)
                part = line.split()

                date_object = datetime.strptime(part[0], "%Y-%m-%d").date()
                time_object = datetime.strptime(part[1], "%H:%M:%S").time()

                if start_date and date_object < start_date:
                    continue
                if end_date and date_object > end_date:
                    continue

                if date_object not in log_dict:
                    log_dict[date_object] = {}
                
                if time_object not in log_dict[date_object]:
                    log_dict[date_object][time_object] = {}
                
                if part[2] not in log_dict[date_object][time_object]:
                    log_dict[date_object][time_object][part[2]] = []

                log_dict[date_object][time_object][part[2]].append(part[3:])
            
def search_log(day_date: date = None, ev_time: time = None, warning: str = None, keywords: str = None, ):
    for day, value in log_dict.items():
        if day_date is None or day==day_date:
            for event_time, events in value.items():
                if ev_time is None or event_time == ev_time:
                    for event_type, event_list in events.items():
                        if warning is None or event_type == warning:
                            if keywords is None or any(keywords.casefold() in "".join(item).casefold() for item in event_list):
                                print(f"{day} {event_time} {event_type} {", ".join(" ".join(event) for event in event_list)}")
                        
def get_totals(provided_date: date = None):

    INFO = 0
    WARNING = 0
    ERROR = 0
    date_range = []
    date_of_day = None
    
    for day, value in log_dict.items():
        if provided_date is None or day == provided_date:
            if provided_date is not None:
                date_of_day = provided_date
            else:
                date_range.append(day)
            for event_time, events in value.items():
                for event_type, event_list in events.items(): 

                    count = len(event_list)
                    if event_type == "INFO":
                        INFO +=count
                    elif event_type == "ERROR":
                        ERROR +=count
                    elif event_type == "WARNING":
                        WARNING +=count

    if provided_date is not None:    
        return(date_of_day,INFO,WARNING,ERROR)
    else:
        return((min(date_range),max(date_range)),INFO,WARNING,ERROR)

def get_most_error(provided_date: date = None):
    errors_str = []
    for day, value in log_dict.items():
        if provided_date is None or provided_date == day:
            for event_time, events in value.items():
                for event_type, event_list in events.items():
                    if event_type == "ERROR":
                        for events in event_list:
                            errors_str.append(" ".join(events))
                    
    error_counts = Counter(errors_str)
    return error_counts.most_common(1)[0]
    
def get_keywords(provided_date: date = None):

    words_list = []
    for day, value in log_dict.items():
        if provided_date is None or provided_date == day:
            for event_time, events in value.items():
                for event_type, event_list in events.items():
                    if event_type == "WARNING":
                        for all_events in event_list:
                            for all_words in all_events:
                                words_list.append(all_words)

    counted_words = Counter(words_list)
    
    return [(item, value) for item, value in counted_words.most_common(3)]                   
    

def event_alert(ev_type: str = None, provided_date: date = None):

    event_string = []

    for day, value in log_dict.items():
        if provided_date is None or provided_date ==day:
            for event_time, events in value.items():
                for event_type, event_list in events.items():
                    if event_type is None or event_type == ev_type:
                        for events in event_list:
                            event_string.append(" ".join(events))
                    
    event_counts = Counter(event_string)

    return [(event, count) for event, count in event_counts.items() 
            if (ev_type == "ERROR" and count >= 5) or 
               (ev_type == "WARNING" and count >= 10)]
   
def generate_report(focus_date: date = None):
    directory_path = "Newprojects/reports"
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    
    file_name = f"daily_report_{datetime.now().strftime("%Y-%m-%d %H-%M-%S")}.txt"
    file_path = os.path.join(directory_path, file_name)

    with open(file_path, "w") as file:
        with redirect_stdout(file):
            print_statistical_summary_insights(focus_date=focus_date)

def data_visualizer(provided_date: date = None):
    totals_for_bar = []
    totals_for_line = []
    event_types = ["INFO", "WARNING", "ERROR"]
    error_counts =[]

    for days, values in log_dict.items():
        totals_for_bar.append(get_totals(provided_date=days))
    
    if len(totals_for_bar)>0:
        for items in sorted(totals_for_bar):
            counts = [items[1], items[2], items[3]]
            plt.figure(figsize=(10, 6))
            plt.bar(event_types, counts, color =["green", "orange", "red"])
            plt.title(items[0])
            plt.xlabel("Event Type")
            plt.ylabel("Count")    
            plt.savefig(f"Newprojects/reports/log_analysis_{items[0].isoformat()}.png")
            plt.close()
    
    for days, values in log_dict.items():

        totals_for_line.append(get_totals())

    if len(totals_for_line)>1:
        error_counts = [items[3] for items in totals_for_line]
        warning_counts = [items[2] for items in totals_for_line]
        days_range = [items[0].strftime("%Y/%m/%d") for items in totals_for_line]
        plt.plot(days_range, error_counts, marker="o", label="Errors", color="red", linewidth=2)
        plt.plot(days_range, warning_counts, marker="s", label="Warnings", color="orange", linewidth=2)
        plt.title("Errors and Warning trends")
        plt.xlabel("Day")
        plt.ylabel("Count")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"Newprojects/reports/log_analysis.png")
        plt.close()            

def save_json(provided_date: date = None):

    directory_path = "Newprojects/reports"
    file_name = f"json_log.json"
    file_path = os.path.join(directory_path, file_name)

    totals = print_statistical_summary_insights(focus_date=provided_date)
    if isinstance(totals[0], tuple):
        log_entry = {
        "date": (totals[0][0].isoformat(), totals[0][1].isoformat()), "INFO": totals[1], "WARNING": totals[2], "ERROR": totals[3]
        }
        
    else:
        log_entry = {
        "date": totals[0].isoformat(), "INFO": totals[1], "WARNING": totals[2], "ERROR": totals[3]
        }

    data = []
    if os.path.exists(file_path):
        with open(file_path, "r") as json_file:
            try:
                data = json.load(json_file)
            except json.JSONDecodeError:
                data = []

    data.append(log_entry)

    with open(file_path, "w") as json_file:
        json.dump(data, json_file, indent=4)
    
    data_visualizer(provided_date=provided_date)

def print_statistical_summary_insights(focus_date: date = None):
    
    if focus_date is None:
        date_list = list(log_dict.keys())
        if not date_list:
            print("No logs available.")
        else:
            min_date = min(date_list)
            max_date = max(date_list)
            total_logs = len(lines_list)
            if min_date == max_date:
                print(f"Total logs: {total_logs} on {min_date}")
            else:
                print(f"Total logs: {total_logs} from {min_date} to {max_date}")

        totals_of_day = get_totals()
        print(f"INFO: {totals_of_day[1]} | WARNING: {totals_of_day[2]} | ERROR: {totals_of_day[3]}")
        print()

        # --- Range Summary ---
        print(f"{totals_of_day[0][0]} - {totals_of_day[0][1]} -> INFO: {totals_of_day[1]} | WARNING: {totals_of_day[2]} | ERROR: {totals_of_day[3]}")
        print()
        
        # --- Most frequent error ---
        most_error = get_most_error()
        print(f"Most frequent error: {most_error[0]} ({most_error[1]} times)")
        print()

        # --- Top 3 warning keywords ---
        top_keywords = get_keywords()
        print("Top 3 Warning keywords:")
        for word, count in top_keywords:
            print(f"{word} ({count})")
        print()

        # --- Alerts ---
        error_alerts = event_alert("ERROR")
        warning_alerts = event_alert("WARNING")
        if error_alerts or warning_alerts:
            print("Alerts:")
        for alert in error_alerts:
            print(f"ALERT: ERROR {alert[0]} occurred {alert[1]} times!")
        for alert in warning_alerts:
            print(f"ALERT: WARNING {alert[0]} occurred {alert[1]} times!")
        print()

        # --- total warnings/errors ---
        print("Total Warnings:")
        search_log(warning="WARNING")
        print("Total Errors:")
        search_log(warning="ERROR")
        print()

        # --- Keyword filtered logs ---
        print("Disk-related logs:")
        search_log(keywords="disk")
        print()

        # --- Report generation timestamp ---
        print(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    else:
        date_picked = focus_date

        if focus_date in log_dict:
        # Count all events for that day
            total_logs = sum(len(events) for times in log_dict[focus_date].values() for events in times.values())
            print(f"Total logs: {total_logs} on {date_picked}")
        else:
            print(f"No logs for {date_picked}")

        totals_of_day = get_totals(provided_date=date_picked)
        print(f"INFO: {totals_of_day[1]} | WARNING: {totals_of_day[2]} | ERROR: {totals_of_day[3]}")
        print()

        # --- Daily Summary ---
        print(f"{totals_of_day[0]} -> INFO: {totals_of_day[1]} | WARNING: {totals_of_day[2]} | ERROR: {totals_of_day[3]}")
        print()

        # --- Most frequent error ---
        most_error = get_most_error(provided_date=date_picked)
        print(f"Most frequent error: {most_error[0]} ({most_error[1]} times)")
        print()

        # --- Top 3 warning keywords ---
        top_keywords = get_keywords(provided_date=date_picked)
        print("Top 3 Warning keywords:")
        for word, count in top_keywords:
            print(f"{word} ({count})")
        print()

        # --- Alerts ---
        error_alerts = event_alert(provided_date=focus_date, ev_type= "ERROR")
        warning_alerts = event_alert(provided_date=focus_date, ev_type= "WARNING")
        if error_alerts or warning_alerts:
            print("Alerts:")
        for alert in error_alerts:
            print(f"ALERT: ERROR {alert[0]} occurred {alert[1]} times!")
        for alert in warning_alerts:
            print(f"ALERT: WARNING {alert[0]} occurred {alert[1]} times!")
        print()

        # --- total warnings/errors ---
        print("Total Warnings:")
        search_log(day_date=date_picked, warning="WARNING")
        print("Total Errors:")
        search_log(day_date=date_picked, warning="ERROR")
        print()

        # --- Keyword filtered logs ---
        print("Disk-related logs:")
        search_log(day_date=date_picked, keywords="disk")
        print()

        # --- Report generation timestamp ---
        print(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


    return totals_of_day

if __name__ == "__main__":
    lines_list=[]
    log_dict={}
    f_path = "Newprojects/serverlogs"
    start = date(2025,11,9)
    end = date(2025,11,12)
    read_log_file(f_path, start_date=start, end_date=end)
    # print_summary(ev_time=time(8,17,45), warning= "WARNING", keywords="space")
    # date_for_summary = date(2025,11,11)
    # print_statistical_summary_insights(focus_date=date_for_summary)
    # generate_report(focus_date=date_for_summary)
    # save_json(provided_date=date_for_summary)
    data_visualizer()
    
    
    
    

# Potential improvements / minor issues:

# Event alert threshold:

# Right now thresholds are hard-coded (>=5 for errors, >=10 for warnings). Consider making these parameters in event_alert() to make your code more flexible for stage 5 features.

# get_most_error() crash possibility:

# If there are no errors for the selected date, Counter(...).most_common(1)[0] will throw IndexError. You might want to check if errors_str: first and handle empty case with something like ("None", 0).

# lines_list vs focus_date totals:

# In range mode, total_logs = len(lines_list) still counts all logs read in lines_list, not filtered by date range. This is fine if your read_log_file was already filtered, but if you ever read all logs without filtering and call print_statistical_summary_insights(focus_date=...), total_logs will include logs from other dates.

# You already fixed single-day totals correctly. Might want to clarify / rename lines_list or filter it by date if you want perfect consistency.

# Repeated printing of "Top 3 Warning keywords:":

# Both inside get_keywords() (prints once) and then again in print_statistical_summary_insights. The inner print in get_keywords() is redundant if your main function is already printing the heading.

# event_alert(ev_type=None, provided_date=None):

# Works fine now, but the check if event_type is None or event_type == ev_type could be simplified: just pass ev_type and skip None case entirely. Otherwise, if ev_type is None, it will match everything.

# Minor formatting nitpicks:

# "Total logs: {total_logs} from {min_date} to {max_date}" – consider formatting dates for readability.

# Your JSON saves ISO format, which is perfect.