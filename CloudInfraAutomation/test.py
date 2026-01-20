import os
import glob

ext = ".ica"
path = r"C:\Users\44746\Downloads"

files = glob.glob(os.path.join(path, f"{ext}"))


print(len(files))

for file_path in files:
    os.remove(file_path)