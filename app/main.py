import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI(title="WORM Logging Service", description="An immutable, append-only logging API")

LOG_FILE_PATH = os.path.abspath("/data/worm_store.log")


class LogEntry(BaseModel):
    source: str
    message: str


# Check that the log file exists at startup
@app.on_event("startup")
def startup_event():
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "w") as f:
            f.write(f"[{datetime.utcnow().isoformat()}] WORM Storage Initialized.\n")


@app.get("/")
def read_root():
    """Landing page to guide users to the documentation."""
    return {
        "title": "WORM Logging System for unerasable logs",
        "status": "online",
        "project": "WORM Logging System for unerasable logs",
        "message": "To interact with the WORM Logging System and review endpoints, please navigate to /docs"
    }


@app.post("/logs", status_code=status.HTTP_201_CREATED)
def write_logs(entry: LogEntry):
    """WORM Operation: Append Only."""
    timestamp = datetime.utcnow().isoformat()
    log_line = f"[{timestamp}] [{entry.source.upper()}] {entry.message}\n"

    try:
        # Open the log file in 'a' (append) mode
        with open(LOG_FILE_PATH, "a") as f:
            f.write(log_line)
        return {"status": "success", "message": "Log securely appended."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")


@app.get("/logs")
def read_logs():
    """Allows reading of the WORM data."""
    if not os.path.exists(LOG_FILE_PATH):
        return {"logs": []}
    with open(LOG_FILE_PATH, "r") as f:
        lines = f.readlines()
    return {"logs": [line.strip() for line in lines]}


# WORM protection
@app.delete("/logs")
@app.put("/logs")
def block_modification():
    """Explicitly blocks any attempts to delete or modify logs via the API."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="WORM Policy Violation: Existing logs cannot be deleted or modified."
    )
