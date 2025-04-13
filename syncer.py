import subprocess, os, logging
from datetime import datetime

LOCAL_FILE = "/home/pfuentes/Documents/keepassxc/1689/myPasswords"
REMOTE_FILE = "google_drive_keepass:Pedro/KeePass/myPasswords"

def get_file_modification_time(file_path, is_remote=False):
    try:
        if is_remote:
            # Use rclone lsl to get remote file info
            result = subprocess.run(
                ["rclone", "lsl", file_path],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                info = result.stdout.split(maxsplit=4)
                # removes last 3 chars (some millisecond shit)
                return datetime.strptime(f"{info[1]} {info[2][:-3]}", "%Y-%m-%d %H:%M:%S.%f")
            else:
                return None  # File not found remotely
        else:
            return datetime.fromtimestamp(os.path.getmtime(file_path))
    except Exception as e:
        print(f"Error retrieving modification time for {'remote' if is_remote else 'local'} file: {e}")
        return None
    
def copy_file(source, destination):
    try:
        subprocess.run(
            ["rclone", "copyto", source, destination],
            check=True
        )
        print(f"Copied file from {source} to {destination}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to copy file from {source} to {destination}: {e}")

def are_times_equal(date1, date2):
    return date1.replace(second=0, microsecond=0) == date2.replace(second=0, microsecond=0)
   

def setup_logger():
    logger = logging.getLogger("syncer")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler("/home/pfuentes/Documents/keepassxc/1689/rclone.log")
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
        local_mod_time = get_file_modification_time(self.local_file, is_remote=False)
        remote_mod_time = get_file_modification_time(self.remote_file, is_remote=True)

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
            backup_file_path = f"/home/pfuentes/Documents/keepassxc/backups/{local_file_basename}_{modification_time.strftime('%Y%m%d_%H%M%S')}"
            copy_file(self.local_file, backup_file_path)
        except Exception as e:
            print(f"Failed to backup local file: {e}")



if __name__ == "__main__":
    logger = setup_logger()

    syncer = FileSyncer(LOCAL_FILE, REMOTE_FILE, logger)
    syncer.sync_files()