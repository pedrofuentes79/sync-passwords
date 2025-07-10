import json, plistlib, os

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


if __name__ == "__main__":
    generate_plist() 