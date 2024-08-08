import os
import sys

# os.system("python PloitZ.py")


current_directory = os.getcwd()

print("Current Working Directory:", current_directory)

script_path = os.path.join(current_directory, "PloitZ", "PloitZ.py")

os.system(script_path)
sys.exit()
