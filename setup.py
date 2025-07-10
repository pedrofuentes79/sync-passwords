import json, plistlib, os, platform
import subprocess
import sys  # new import for sys.executable

LOG_PATH = "rclone.log"
CONFIG_PATH = "config.json"
MOUNT_PLIST_PATH = "com.pedranji.sync-passwords.plist"
HOURLY_PLIST_PATH = "com.pedranji.sync-passwords.hourly.plist"

def generate_plist(config_path: str = CONFIG_PATH, output_path: str = MOUNT_PLIST_PATH) -> None:
    """Generate a launchd plist file using parameters from config.json."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at {config_path}")

    with open(config_path) as f:
        cfg = json.load(f)

    plist_dict = {
        "Label": "com.rclone.mount",
        "ProgramArguments": [
            "/usr/local/bin/rclone",
            "mount",
            f"{cfg['remote_name']}:",
            cfg["remote_folder_local_path"],
            "--allow-non-empty",
        ],
        "RunAtLoad": True,
    }

    with open(output_path, "wb") as fp:
        plistlib.dump(plist_dict, fp)

    print(f"Written launchd plist to {output_path}")


def generate_hourly_run_plist(minute: int = 15, output_path: str = HOURLY_PLIST_PATH) -> None:
    """Generate a launchd plist to run syncer.py at a specified minute each hour."""
    python_exe = sys.executable
    syncer_path = os.path.abspath("syncer.py")

    plist_dict = {
        "Label": "com.pedranji.sync-passwords.syncer",
        "ProgramArguments": [python_exe, syncer_path],
        "StartCalendarInterval": {"Minute": minute},  # every hour at the given minute
        "StandardOutPath": os.path.abspath("syncer.log"),
        "StandardErrorPath": os.path.abspath("syncer.log"),
    }

    with open(output_path, "wb") as fp:
        plistlib.dump(plist_dict, fp)

    print(f"Written syncer launchd plist to {output_path}")


def load_launchd_job(plist_path: str) -> None:
    """Load (or reload) the launchd job defined by the given plist."""
    plist_abspath = os.path.abspath(plist_path)
    try:
        # Use -w to persist the load across reboots
        subprocess.run(["launchctl", "load", "-w", plist_abspath], check=True)
        print(f"Loaded launchd job from {plist_abspath}")
    except subprocess.CalledProcessError as exc:
        print(f"Failed to load launchd job: {exc}")


def setup_hourly_job() -> None:
    system = platform.system()
    python_exe = sys.executable
    syncer_abs_path = os.path.abspath("syncer.py")

    if system == "Darwin":
        # macOS: create and load a launchd plist that runs syncer.py at minute 15 every hour
        generate_hourly_run_plist(minute=15, output_path=HOURLY_PLIST_PATH)
        load_launchd_job(plist_path=HOURLY_PLIST_PATH)
    elif system == "Linux":
        # Linux: set up a cron job that runs syncer.py hourly at minute 0
        log_path = os.path.abspath(LOG_PATH)
        cron_line = f"0 * * * * {python_exe} {syncer_abs_path} >> {log_path} 2>&1 # sync-passwords"

        try:
            # Fetch existing crontab (if any)
            res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            existing_cron = res.stdout if res.returncode == 0 else ""
        except FileNotFoundError:
            print("crontab command not found. Please install cron or add the entry manually.")
            return

        if cron_line.strip() in existing_cron:
            print("Cron entry already present. No changes made.")
            return

        new_cron = existing_cron.strip() + ("\n" if existing_cron.strip() else "") + cron_line + "\n"
        # Install new crontab
        subprocess.run(["crontab", "-"], input=new_cron, text=True, check=True)
        print("Cron entry added to run syncer.py hourly.")
    else:
        raise ValueError(f"Unsupported system: {system}")


if __name__ == "__main__":
    # Regenerate mount plist (if applicable) and load it
    # generate_plist(output_path=MOUNT_PLIST_PATH)
    # load_launchd_job(MOUNT_PLIST_PATH)

    # Set up hourly job for syncer.py
    setup_hourly_job()