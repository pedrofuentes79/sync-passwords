import json, plistlib, os
import subprocess

CONFIG_PATH = "config.json"
PLIST_PATH = "com.pedranji.sync-passwords.plist"


def generate_plist(config_path: str = CONFIG_PATH, output_path: str = PLIST_PATH) -> None:
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


def load_launchd_job(plist_path: str = PLIST_PATH) -> None:
    """Load (or reload) the launchd job defined by the given plist."""
    plist_abspath = os.path.abspath(plist_path)
    try:
        # Use -w to persist the load across reboots
        subprocess.run(["launchctl", "load", "-w", plist_abspath], check=True)
        print(f"Loaded launchd job from {plist_abspath}")
    except subprocess.CalledProcessError as exc:
        print(f"Failed to load launchd job: {exc}")


if __name__ == "__main__":
    generate_plist()
    load_launchd_job() 