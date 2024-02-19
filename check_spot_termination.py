import time
from subprocess import call

import requests


def check_spot_termination():
    """Check for Spot Instance termination notice."""
    termination_url = "http://169.254.169.254/latest/meta-data/spot/instance-action"
    try:
        response = requests.get(termination_url, timeout=2)
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        pass
    return False


def graceful_shutdown():
    """Initiate a graceful shutdown of the Celery worker."""
    # Replace `celery_worker_name` with the actual name of your worker
    call(["pkill", "-9", "celery"])


if __name__ == "__main__":
    while True:
        if check_spot_termination():
            print("Spot Instance termination notice detected. Initiating graceful shutdown.")
            graceful_shutdown()
            break
        time.sleep(30)  # Check every 30 seconds
