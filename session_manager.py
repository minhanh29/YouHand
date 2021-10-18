import os
import shutil
import time


def check_storage(session_id):
    '''
    Check if session_id is still in use
    '''
    return os.path.isdir(f"./temp/{session_id}")


def create_storage(session_id):
    target_dir = f"./temp/{session_id}"
    os.mkdir(target_dir)
    shutil.copyfile("./database/directed_gesture.json",
                    f"{target_dir}/directed_gesture.json")
    shutil.copyfile("./database/undirected_gesture.json",
                    f"{target_dir}/undirected_gesture.json")
    shutil.copyfile("./database/static_command_db.json",
                    f"{target_dir}/static_command_db.json")

    # add creating time for expiry check
    start_time = int(time.time())
    with open(os.path.join(target_dir, "lifetime.txt"), "w") as f:
        f.write(str(start_time))


def clean_storage():
    if not os.path.isdir("./temp"):
        os.mkdir("./temp")
        return

    # get all available sessions
    session_list = os.listdir("./temp")
    session_list = [s for s in session_list if os.path.isdir(f"./temp/{s}")]
    for session_id in session_list:
        # read the lifetime
        my_path = os.path.join("./temp", session_id)
        with open(os.path.join(my_path, "lifetime.txt"), "r") as f:
            start_time = f.read()

        start_time = int(start_time)
        if int(time.time() - start_time) < 900:
            continue

        # delete data
        shutil.rmtree(my_path)
