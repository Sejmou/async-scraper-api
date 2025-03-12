import os


def is_file_empty(file_path):
    """Checks if a given file is empty. Performs naive file size check and potentially additional checks depending on the file extension."""
    if os.path.getsize(file_path) == 0:
        return True
    if file_path.endswith(".jsonl"):
        # read first line of the file and check if it's empty
        with open(file_path, "r") as f:
            first_line = f.readline()
        return first_line.strip() == ""
    return False
