from datetime import datetime, timedelta, date, time
from collections import Counter
from contextlib import redirect_stdout

def read_log_file(file_path: str):
    with open("Newprojects/" + file_path, "r") as log_file:
        for line in log_file:
            line = line.strip()
            lines_list.append(line)
            part = line.split()   
            date_object = datetime.strptime(part[0], "%Y-%m-%d").date()
            time_object = datetime.strptime(part[1], "%H:%M:%S").time()

            if date_object not in log_dict:
                log_dict[date_object] = {}
            
            if time_object not in log_dict[date_object]:
                log_dict[date_object][time_object] = {}
            
            if part[2] not in log_dict[date_object][time_object]:
                log_dict[date_object][time_object][part[2]] = []

            log_dict[date_object][time_object][part[2]].append(part[3:])


def print_summary(day_date: date = None, ev_time: time = None, warning: str = None, keywords: str = None, ):
    for day, value in log_dict.items():
        if day_date is None or day==day_date:
            for event_time, events in value.items():
                if ev_time is None or event_time == ev_time:
                    for event_type, event_list in events.items():
                        if warning is None or event_type == warning:
                            if keywords is None or any(keywords in "".join(item) for item in event_list):
                                print(f"{day} {event_time} {event_type} {event_list}")
                        
def print_totals():
    INFO = 0
    WARNING = 0
    ERROR = 0
    for day, value in log_dict.items():
        for event_time, events in value.items():
            for event_type, event_list in events.items():
                if event_type == "INFO":
                    INFO +=1
                if event_type == "ERROR":
                    ERROR +=1
                if event_type == "WARNING":
                    WARNING +=1
    
    print(f"Total logs: {len(lines_list)}")
    print(f"INFO: {INFO} | WARNING: {WARNING} | ERROR: {ERROR}")

    # def print_totals():
    # counts = {"INFO": 0, "WARNING": 0, "ERROR": 0}

    # for value in log_dict.values():
    #     for events in value.values():
    #         for event_type in events.keys():
    #             if event_type in counts:
    #                 counts[event_type] += 1

    # total_logs = sum(counts.values())
    # print(f"Total logs: {total_logs}")
    # print(" | ".join(f"{k}: {v}" for k, v in counts.items()))


def statistical_summary_insights():
    day_list = []
    
    for day, value in log_dict.items():
        INFO = 0
        WARNING = 0
        ERROR = 0
        for event_time, events in value.items():
            for event_type, event_list in events.items():
                if event_type == "INFO":
                    INFO +=1
                if event_type == "ERROR":
                    ERROR +=1
                if event_type == "WARNING":
                    WARNING +=1
        day_list.append((f"{day} -> INFO: {INFO} | ERROR: {ERROR} | WARNING: {WARNING}"))

    for item in day_list:
        print(item)
    
    print()

    for day, value in log_dict.items():
        errors_string = []
        for event_time, events in value.items():
            for event_type, event_list in events.items():
                if event_type == "ERROR":
                    for events in event_list:
                        errors_string.append(" ".join(events))
                    
    error_counts = Counter(errors_string)
    most_common_error = error_counts.most_common(1)
    print(f"Most frequent error: {most_common_error[0][0]} ({most_common_error[0][1]} times)")
    
    print()

    words_list = []
    for day, value in log_dict.items():
        for event_time, events in value.items():
            for event_type, event_list in events.items():
                if event_type == "WARNING":
                    for all_events in event_list:
                        for all_words in all_events:
                            words_list.append(all_words)

    counted_words = Counter(words_list)
    print("Top 3 Warning keywords:")                   
    for item, value in counted_words.most_common(3):
        print(f"{item} ({value})")
    print()


def generate_report():
    with open("Newprojects/daily_summary.txt", "w") as file:
        with redirect_stdout(file):
            print_totals()
            print()
            statistical_summary_insights()
            print(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
         

if __name__ == "__main__":
    lines_list=[]
    log_dict={}
    read_log_file("server.log")
    # print_summary(ev_time=time(8,17,45), warning= "WARNING", keywords="space")
    print_totals()
    print()
    statistical_summary_insights()
    generate_report()
    
    

