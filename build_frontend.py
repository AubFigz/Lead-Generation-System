import os
from shutil import copyfile

def build_frontend(static_path, build_path):
    os.makedirs(build_path, exist_ok=True)
    for file_name in os.listdir(static_path):
        if file_name.endswith(".css") or file_name.endswith(".js"):
            src = os.path.join(static_path, file_name)
            dest = os.path.join(build_path, file_name)
            copyfile(src, dest)
    print("Frontend assets built successfully.")

if __name__ == "__main__":
    build_frontend("./static", "./build")
