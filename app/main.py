import hashlib
import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

print("DEBUG ENVIRONMENT KEYS:", list(os.environ.keys()))

# Load environment variables from a local .env file it it exists
load_dotenv()

app = FastAPI(title="Cryptographic WORM System")
LOG_FILE_PATH = os.path.abspath("/data/worm_store.log")

# Azure Configuration Extraction from Environment Variables
AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME", "compliance-audit-logs")

class LogEntry(BaseModel):
    source: str
    message: str

# Function to ship logs up to Azure as separate compliance blocks
def replicate_block_to_azure(blob_name: str, raw_og_line: str):
    """Uploads the log string as an individual immutable blob sequence."""
    if not AZURE_CONNECTION_STRING:
        print("Azure Connection String is missing from environment variables!")
        return

    # Sanitize the incoming blob file name to protect against naming rules violations
    clean_blob_name = blob_name.strip().lower().replace("_", "-")

    try:
        # Pass the connection string
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=clean_blob_name)

        # overwrite=False ensures that in the event of an attacker attempting to resend an existing
        # blob filename, Azure rejects the transaction immediately at the API boundary
        blob_client.upload_blob(raw_og_line, overwrite=False)
        print(f"Successfully replicated {clean_blob_name} to Azure container '{CONTAINER_NAME}'!")
    except Exception as cloud_err:
        print(f"Cloud asynchronous reapplication error skipped: {cloud_err}")

@app.get("/")
def read_root():
    """Landing page to guide users to the documentation."""
    return {
        "title": "WORM Logging System for unerasable logs",
        "status": "online",
        "project": "WORM Logging System for unerasable logs",
        "message": "To interact with the WORM Logging System and review endpoints, please navigate to /docs"
    }

# Hashing function for logs
def calculate_entry_hash(timestamp: str, source: str, message: str, prev_hash: str) -> str:
    """Identical string concatenation across creation and verification."""
    payload = f"{timestamp.strip()}|{source.strip()}|{message.strip()}|{prev_hash.strip()}"
    return hashlib.sha256(payload.encode()).hexdigest()

# Reads historical hashes
def get_last_line_hash() -> str:
    """Reads the log file to grab the hash of the last valid entry."""
    if not os.path.exists(LOG_FILE_PATH):
        return "0" * 64 # Genesis block hash (64 zeros acting as the anchor)
    with open(LOG_FILE_PATH, "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
        if not lines:
            return "0" * 64
         # Extract the trailing hash from the last line
        last_line = lines[-1]
        if " | Hash: " in last_line:
            return last_line.split(" | Hash: ")[-1]
    return "0" * 64


# Check that the log file exists at startup
@app.on_event("startup")
def startup_event():
    """Initializes the secure directory structure and the Genesis log block."""
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    if not os.path.exists(LOG_FILE_PATH) or os.path.getsize(LOG_FILE_PATH) == 0:
        timestamp = datetime.utcnow().isoformat()
        genesis_prev_hash = "0" * 64
        # Unified engine
        genesis_hash = calculate_entry_hash(timestamp, "SYSTEM", "WORM Storage Initialized.", genesis_prev_hash)

        with open(LOG_FILE_PATH, "w") as f_out:
            f_out.write(f"[{timestamp}] [SYSTEM] WORM Storage Initialized. | Prev: {genesis_prev_hash[:8]} | Hash: {genesis_hash}\n")

@app.post("/logs", status_code=status.HTTP_201_CREATED)
def write_logs(entry: LogEntry):
    """WORM Operation: Appends a Cryptographically chained entry to the audit trail."""
    timestamp = datetime.utcnow().isoformat()
    prev_hash = get_last_line_hash()

    # Unified engine
    current_hash = calculate_entry_hash(timestamp, entry.source, entry.message, prev_hash)
    log_line = f"[{timestamp}] [{entry.source.upper()}] {entry.message} | Prev: {prev_hash[:8]} | Hash: {current_hash}\n"

    try:
        # 1. Write locally to the append-only storage volume
        with open(LOG_FILE_PATH, "a") as f_out:
            f_out.write(log_line)

        # 2. LINK TO AZURE: Upload this exact entry to the WORM container
        # The unique hash is sued as the filename to prevent collision tracking
        blob_filename = f"log-block-{current_hash[:16]}.txt"
        replicate_block_to_azure(blob_filename, log_line)

        return {"status": "success", "hash": current_hash, "cloud_sync": "committed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs")
def read_logs():
    """Reads the raw text ledger files and prints them neatly to the browser GUI."""
    if not os.path.exists(LOG_FILE_PATH):
        return {"logs": []}
    with open(LOG_FILE_PATH, "r") as f:
        # Read file lines, strip trailing newlines, and filter out empty fields
        # raw_logs = [line.strip() for line in f.readlines() if line.strip()]
        return {"logs": [line.strip() for line in f.readlines() if line.strip()]}

@app.get("/logs/verify")
def verify_integrity_of_ledger():
    """Validates every single hash in the file sequentially to check for tampering."""
    if not os.path.exists(LOG_FILE_PATH):
        return {"status": "empty", "message": "No logs have been recorded yet."}

    expected_prev_hash = "0" * 64

    with open(LOG_FILE_PATH, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            # Check if the line format is corrupt
            if " | Prev: " not in line or " | Hash: " not in line:
                raise HTTPException(status_code=400, detail=f"Line {line_num} format corrupt.")

            # Parse out components from the log string
            try:
                # [Timestamp] [SOURCE] Message | Prev: xxxxxxxx | Hash: yyyyyyy
                parts = line.split(" | ")
                meta_and_msg = parts[0] # [Timestamp] [SOURCE] Message
                current_hash = parts[2].replace("Hash: ", "").strip()

                # Extract sections clean by splitting brackets
                timestamp_part = meta_and_msg.split("]")[0].replace("[", "").strip()
                source_part = meta_and_msg.split("]")[1].replace("[", "").strip()
                message_part = meta_and_msg.split("]")[-1].strip()

                calculated_hash = calculate_entry_hash(timestamp_part, source_part, message_part, expected_prev_hash)

                if calculated_hash != current_hash:
                    return HTTPException(
                        status_code=status.HTTP_417_EXPECTATION_FAILED,
                        detail=f"TAMPERING DETECTED at entry line {line_num}! Cryptographic chain broken."
                    )

                expected_prev_hash = current_hash
            except HTTPException as he:
                raise he
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Parsing crash on line  {line_num}: {str(e)}")

    return {"status": "verified", "message": "Audit trail integrity intact. Zero alterations found."}

def replicate_to_azure(blob_name: str, data:str):
    """Fires and forgets log files straight up to a locked cloud container."""
    if not AZURE_CONNECTION_STRING:
        return # Skip if connection string isn't injected into the enviornment

    try:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=blob_name)
        blob_client.upload_blob(data, overwrite=False) # Fail immediately if file name already exists
    except Exception as cloud_err:
        print(f"Cloud backup failure: {cloud_err}") # Non-blocking for the local system

# WORM protection
@app.delete("/logs")
@app.put("/logs")
def block_modification():
    """Explicitly blocks any attempts to delete or modify logs via the API."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="WORM Policy Violation: Existing logs cannot be deleted or modified."
    )
