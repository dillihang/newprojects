from datetime import datetime
import os

os.makedirs("/data", exist_ok=True)

with open("/data/myfile.txt", "a") as f:
    f.write(f"Entry at {datetime.now()}\n")

print("data written")