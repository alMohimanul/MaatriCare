import subprocess
import os
from Utils.logging_config import init_logging


def launch_ui():
    logger = init_logging()
    logger.info("🚀 Starting MaatriCare UI Application")

    ui_path = os.path.join("UI", "ui.py")
    try:
        logger.info(f"📱 Launching Streamlit UI from: {ui_path}")
        subprocess.run(["streamlit", "run", ui_path])
    except Exception as e:
        logger.error(f"❌ Failed to launch UI: {e}")
        raise
    finally:
        from Utils.logging_config import log_shutdown

        log_shutdown()


if __name__ == "__main__":
    launch_ui()
