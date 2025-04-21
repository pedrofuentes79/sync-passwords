import os, logging, json, shutil
from datetime import datetime

with open("config.json", "r") as f:
    config = json.load(f)

LOCAL_FILE = config["local_password_file_path"]
MOUNTED_REMOTE_FILE = f"{config['remote_folder_local_path']}/{config['remote_password_file_name']}"

def get_file_modification_time(file_path):
    try:
        return datetime.fromtimestamp(os.path.getmtime(file_path))
    except Exception as e:
        print(f"Error retrieving modification time for file {file_path}: {e}")
        return None
    
def copy_file(source, destination):
    try:
        shutil.copy2(source, destination)
        print(f"Copied file from {source} to {destination}")
    except Exception as e:
        print(f"Failed to copy file from {source} to {destination}: {e}")

def are_times_equal(date1, date2):
    return date1.replace(second=0, microsecond=0) == date2.replace(second=0, microsecond=0)
   
def setup_logger():
    logger = logging.getLogger("syncer")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler("rclone.log")
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

class FileSyncer:
    def __init__(self, local_file, remote_file, logger):
        self.local_file = local_file
        self.remote_file = remote_file
        self.logger = logger

    def sync_files(self):
        local_mod_time = get_file_modification_time(self.local_file)
        remote_mod_time = get_file_modification_time(self.remote_file)

        # Check which file to sync
        if local_mod_time and remote_mod_time:
            if are_times_equal(local_mod_time, remote_mod_time):
                self.logger.info("Both files are up-to-date (minute-level). No sync needed.")
            elif local_mod_time > remote_mod_time:
                self.logger.info("Local file is newer. Syncing to remote.")
                copy_file(self.local_file, self.remote_file)
            else:
                self.logger.info("Remote file is newer. Syncing to local.")
                self.backup_local_file(local_mod_time)
                copy_file(self.remote_file, self.local_file)
        elif local_mod_time:
            self.logger.info("Remote file is missing. Syncing local file to remote.")
            copy_file(self.local_file, self.remote_file)
        elif remote_mod_time:
            self.logger.info("Local file is missing. Syncing remote file to local.")
            copy_file(self.remote_file, self.local_file)
        else:
            self.logger.info("Both files are missing. Nothing to sync.")

    def backup_local_file(self, modification_time: datetime):
        try:
            local_file_basename = os.path.basename(self.local_file)
            backup_dir = os.path.join(os.path.dirname(self.local_file), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            backup_file_path = os.path.join(backup_dir, f"{local_file_basename}_{modification_time.strftime('%Y%m%d_%H%M%S')}")
            copy_file(self.local_file, backup_file_path)
        except Exception as e:
            print(f"Failed to backup local file: {e}")

if __name__ == "__main__":
    logger = setup_logger()
    syncer = FileSyncer(LOCAL_FILE, MOUNTED_REMOTE_FILE, logger)
    syncer.sync_files()