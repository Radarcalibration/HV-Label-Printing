import csv
import os
import threading
from datetime import date, time

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Machine Data API")

# ================== EDIT THESE VALUES ==================
CSV_FILE = "machine_data.csv"
# =======================================================

FIELDS = [
    "date",
    "time",
    "line_number",
    "process_code",
    "process_name",
    "machine_number",
    "machine_name",
    "part_serial_number",
    "status",
]

csv_lock = threading.Lock()  # prevents two requests writing at the same time


class MachineData(BaseModel):
    date: date
    time: time
    line_number: str
    process_code: str
    process_name: str
    machine_number: str
    machine_name: str
    part_serial_number: str
    status: str


def save_to_csv(row: dict):
    with csv_lock:
        file_exists = os.path.isfile(CSV_FILE) and os.path.getsize(CSV_FILE) > 0
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)


@app.post("/data", status_code=201)
def receive_data(item: MachineData):
    row = item.model_dump()
    row["date"] = row["date"].isoformat()   # 2026-10-21
    row["time"] = row["time"].isoformat()   # 14:30:00

    save_to_csv(row)
    print("Saved:", row)
    return {"message": "Data saved to CSV", "data": row}


@app.get("/data")
def get_all_data():
    if not os.path.isfile(CSV_FILE):
        return []
    with csv_lock:
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))


#  pip install fastapi uvicorn requests
#  uvicorn server:app --host 0.0.0.0 --port 8000 --reload  
# python -m uvicorn server:app --host 0.0.0.0 --port 8001        