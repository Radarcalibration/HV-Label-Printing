import requests
from datetime import datetime

# ================== EDIT THESE VALUES ==================
API_URL = "http://10.0.42.86:8001/data"

LINE_NUMBER        = "L01"
PROCESS_CODE       = "P100"
PROCESS_NAME       = "Assembly"
MACHINE_NUMBER     = "M05"
MACHINE_NAME       = "Press Machine"
PART_SERIAL_NUMBER = "SN000000001"
STATUS             = "OK"        # e.g. OK / NG / RUNNING / STOPPED

# Leave as None to use the current date/time automatically
DATE = None                      # format: "2026-10-21"
TIME = None                      # format: "14:30:00"
# =======================================================


def send_data():
    now = datetime.now()
    payload = {
        "date": DATE or now.strftime("%Y-%m-%d"),
        "time": TIME or now.strftime("%H:%M:%S"),
        "line_number": LINE_NUMBER,
        "process_code": PROCESS_CODE,
        "process_name": PROCESS_NAME,
        "machine_number": MACHINE_NUMBER,
        "machine_name": MACHINE_NAME,
        "part_serial_number": PART_SERIAL_NUMBER,
        "status": STATUS,
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=10, verify=False)
        response.raise_for_status()
        print("Status code:", response.status_code)
        print("Response:", response.json())
    except requests.exceptions.RequestException as e:
        print("Request failed:", e)


if __name__ == "__main__":
    send_data()


# python client.py