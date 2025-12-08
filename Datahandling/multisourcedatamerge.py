import json
import pandas as pd
import os

def read_files(file_A: str, file_B: str):

    try:
        if file_A.endswith(".json"):
            df1 = pd.read_json(file_A)
        else:
            df1 = pd.read_csv(file_A)
        
        print(df1)

        if file_B.endswith(".json"):
            df2 = pd.read_json(file_B)
        else:
            df2=pd.read_csv(file_B)
        
        print(df2)
        
    except Exception as e:
        print(e)
        return

    all_collumns = list(set(df1.columns) | set(df2.columns))

    print(all_collumns)


if __name__ == "__main__":

    file_pathA = "Newprojects/Datahandling/json_data/posts_a.json"
    file_pathB = "Newprojects/Datahandling/json_data/posts_b.json"

    read_files(file_pathA, file_pathB)