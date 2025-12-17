from datetime import datetime, timedelta
import githubapitolistrepos
import pushfiletogitviaapi

def get_data(url: str, header: str):

    if not header:
        print("[ERROR] header could not be retrieved")
        return None
    
    response = pushfiletogitviaapi.check_response(url=url, headers=header)

    if not response:
        print("[ERROR] Could not retrive response data")
        return None

    try:
        data = response.json()
        return data
    except ValueError as e:
        print(f"Invalid JSON: {e}")


def repo_alerts(git_url: str, day_threshold: int):
    
    processed_repo={
        "private_repos": [],
        "none_lang_repos": [],
        "zero_star_repos": [],
        "repo_lastpushedover_ndays":[],
        "archived_repo": [],
        "no_commit": [],
        "notification_triggered": 0
    }

    header = githubapitolistrepos.get_token()

    if not header:
        print("[ERROR] header could not be retrieved")
        return

    data = get_data(url=git_url, header=header)

    if not data:
        print("[ERROR] no data found")
        return

    processed_repo["total_repos"]=len(data)
    
    for repo in data:
        repo_name = repo["name"]
        last_pushed_date = repo["pushed_at"]
        if not last_pushed_date:
            processed_repo["no_commit"].append(repo_name)
            processed_repo["notification_triggered"]+=1
            continue
        else:
            parsed_date = datetime.fromisoformat(last_pushed_date.replace("Z", ""))
            date_threshold = datetime.now() - timedelta(days=day_threshold)
            
        if repo["private"]:
            processed_repo["private_repos"].append(repo_name)
            processed_repo["notification_triggered"]+=1
        if not repo["language"]:
            processed_repo["none_lang_repos"].append(repo_name)
            processed_repo["notification_triggered"]+=1
        if repo["stargazers_count"] == 0:
            processed_repo["zero_star_repos"].append(repo_name)
            processed_repo["notification_triggered"]+=1
        if repo["archived"]:
            processed_repo["archived_repo"].append(repo_name)
            processed_repo["notification_triggered"]+=1
        if parsed_date<date_threshold:
            last_pushed = f"(last push: {parsed_date.strftime("%d/%m/%Y")})"
            processed_repo["repo_lastpushedover_ndays"].append((repo_name, last_pushed))
            processed_repo["notification_triggered"]+=1
        
    return processed_repo

def print_summary(processed_repo: dict):
    
    print(f"=== Github Repo Notifier ===")
    print()
    categories = [
        ("PRIVATE", processed_repo["private_repos"]),
        ("NO LANGUAGE", processed_repo["none_lang_repos"]),
        ("ZERO STARS", processed_repo["zero_star_repos"]),
        ("ARCHIVED", processed_repo["archived_repo"]),
        ("NO COMMITS", processed_repo["no_commit"])
    ]
    
    for label, repos in categories:
        if repos:
            print(f"[{label}] {', '.join(repos)}")
        else:
            print(f"[{label}] None")
    
   
    if processed_repo["repo_lastpushedover_ndays"]:
        for repo, date in processed_repo["repo_lastpushedover_ndays"]:
            print(f"[INACTIVE] {repo} {date}")
    else:
        print("[INACTIVE] None")
    
    print(f"\nTotal repos scanned: {processed_repo["total_repos"]}")
    print(f"Notifications: {processed_repo['notification_triggered']}")

if __name__=="__main__":
    
    url = "https://api.github.com/user/repos"

    new_dict=repo_alerts(git_url=url, day_threshold=30)
    print_summary(processed_repo=new_dict)
