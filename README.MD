# WORM Logging System for Unerasable Logs

A containerized, proof-of-concept **Write Once, Read Many (WORM)** logging
architecture and data integrity compliance.

This project implements a secure logging API that allows applications to safely
append logs while strictly blocking updates, modifications, or deletions at both
the application gateway and storage filesystem levels.

## Security Architecture & WORM Enforcement

Traditional filesystems allow administrators or malicious actors with root
privileges to alter or clear logs to mask unauthorized activity. This system
mitigates that risk using a multi-layered software defined WORM architecture:

1. **API Layer Restriction:** The service exposes `POST` (Write) and `GET` (Read)
operations. It explicitly intercepts and rejects `PUT` (Update) and `DELETE`
(Destroy) requests with a strict `403 Forbidden` policy violation warning.
2. **Sequential Storage Layer Append-Only:** The filesystem interaction uses
Python's unique `a` (append) tracking state. Disk head pointer offsets are bounded
strictly to the end of the existing file descriptor pool, guaranteeing that 
pre-existing log blocks can never be overwritten.
3. **Isolated Environment Layer Bind Mounts:** Storage volumes partition the
logical audit trail safely into a decoupled sandbox, ensuring persistent
tracking of data integrity.
4. **Cryptographic Hash Chaining (SHA-256):** Every log entry dynamically encapsulates
a UTC timestamp, message source, raw text payload, and the exact cryptographic signature
of the preceding block. This forms an unbroken dependency chain anchored to a Genesis 
block.
5. **Hybrid Storage Architecture:** * **Local Layer:** Appends securely to a localized,
persistent volume ledger (`/data/worm_store.log`) for rapid API reads and real-time 
auditing.
6. **Cloud Layer:** Streams individual log blocks to an isolated **Azure Blob Storage Container**
managed under a Time-Based Immutable Retention Policy.

## Tech Stack & Dependencies

* **Backend Framework:** FastAPI (Python 3.10+)
* **Containerization & Environment Sandboxing:** Docker & Docker Compose
* **Cloud Infrastructure Integration:** Azure Blob Storage SDK

## Quick start guide

The environment is completely containerized. No configuration is needed
of local Python virtual environments (`venv`) or manually resolve missing
dependencies.

### Prerequisites

1. Ensure you have [Docker Desktop](https://docs.docker.com/desktop/) installed and
running on your host machine.
2. **Python 3.10 installed**
3. An active **Azure Storage Account** with an isolated Blob Container configured

### 1. Clone the Repository
Open a terminal (PowerShell, Command Prompt, Git Bash) and execute the following:
```bash
git clone [https://github.com/L00197082/worm_logging_project.git](https://github.com/L00197082/work_logging_project.git
```
### 2. Environment Configuration
1. In the root directory, locate the `.env.example` file.
2. Create a copy of this file in the root directory and rename it to `.env`:
```copy 
.env.example .env
```
3. Open up app/.env and populate it with your specific Azure credentials:
AZURE_STORAGE_CONNECTION_STRNG="DefaultEndpointsProtocol=https;AccountName=your_account;AccountKey=your_key;..."
CONTAINER_NAME="your-compliance-container-name"

### 2. Spin Up the Application Environment
``docker-compose up --build``
Leave the terminal window open. Once initialization is complete, a terminal 
confirmation log will indicate that the web server is live:
*INFO: Uvicorn running on http://0.0.0.0:8000*

### 3. Access the Graphical Test Dashboard
Open a web browser and navigate to the API control panel:
*INFO: Uvicorn running on http://0.0.0.0:8000/docs*

The Swagger interface allows you to interact with the core features:
- POST /logs: Submit a new log payload (creates a validated timestamped entry).
- GET /logs: Inspect the entire chronological audit trail.
- DELETE /logs / PUT /logs: Attempt to violate compliance rules to witness the 
- automated system defenses lock down the execution thread.

## Running Automated Compliance Tests

An automated test suite is included to validate the WORM immutability 
constraints are entirely unbreakable and resilient to tampering. 

While the primary docker container is running, open a second terminal window
in the project root directory and run the following command:
``docker-compose exec worm-api pytest app/tests/``

### Test Suite Coverage:
- test_write_and_read_log: Asserts that writing new logs behaves deterministically
and correctly builds audit records.
- test_worm_constraints: Simulates malicious payloads trying to bypass 
authorization to update or delete data. This confirms that the system drops the
connection to the API endpoint with an immutable policy violation flag.

## Clean Shutdown

To exit the runtime environment and stop listening on the network ports, press
Ctrl + C in the primary terminal window. Or execute the following:
```docker-comp```