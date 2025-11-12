from datetime import datetime, timedelta, date, time
from collections import Counter
from contextlib import redirect_stdout
import os
import json
import glob

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
    date_for_summary = date(2025,11,11)
    print_statistical_summary_insights(focus_date=date_for_summary)
    generate_report(focus_date=date_for_summary)
    save_json(provided_date=date_for_summary)
    
    
    
    

