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
copy .env.example .env
```
3. Open up app/.env and populate it with your specific Azure credentials:
AZURE_STORAGE_CONNECTION_STRNG="DefaultEndpointsProtocol=https;AccountName=your_account;AccountKey=your_key;..."
CONTAINER_NAME="compliance-audit-logs"

### 2. Spin Up the Application Environment
``docker-compose up --build -d``
Leave the terminal window open. Once initialization is complete, a terminal 
confirmation log will indicate that the web server is live:

### 3. Access the Graphical Test Dashboard
Open a web browser and navigate to the API control panel:
*INFO: Uvicorn running on http://localhost:8000/docs*

The Swagger interface allows you to interact with the core features:
- POST /logs: Submit a new log payload (creates a validated timestamped entry).
- GET /logs: Inspect the entire chronological audit trail.
- DELETE /logs / PUT /logs: Attempt to violate compliance rules to witness the 
automated system defenses lock down the execution thread.
- GET /logs/verify: Loop through the records line-by-line, computing hashes
sequentially to ensure that the chain is perfectly linked and intact. returning a
clean validation success confirmation.

### 4. Create the storage account in Azure
1. In the Azure dashboard search for 'storage accounts' in the search bar./
2. Select 'create' in the storage account dashboard.
3. Create the new storage account with the following information: 
   1. Choose the relevant subscription.
   2. Resource group: "work-logging-rg"
   3. Storage account name: workstorageleg01 
   4. Region: (Europe) West Europe
   5. Preferred storage stype: Azure Blob Storage or Azure Data Lake Storage
   6. Performance: Standard
   7. Redundancy: Locally Redundant Storage (LRS)
   8. Click review + create then create and wait for deployment.
   9. Once deployment is finished, click **Go to resource**

### 5. Create the Isolated Blob Container
1. On your Storage Account's left-hand sidebar, navigate to the **Data storage** section and click Containers.
2. Click the + **Container** button at the top.
3. In the right-hand panel that opens, configure the properties:
   1. Name: Set this to match your environment variables (e.g., compliance-audit-logs).
   2. Anonymous access level: Set this to Private (no anonymous access). This keeps your compliance ledger 
   fully secure from public view.
4. Click Create.

### 6. Extract the Connection String for the .env file
1. The left-side of the Storage Account, scroll to the Security + networking section.
2. Click on Access Keys.
3. Under Key1, select Connection string now.
4. Click the **Show** button, the click **Copy** to clipboard.
5. Open the project's .env file and paste it directly into the variable field.
## System Validation 

Once the interactive Swagger UI interface resolves at `http://localhost:8000/docs`,
the following functional evaluations can be performed to test the core system 
capabilities:

#### Test A: Ledge Verification & Anchor Validation (`GET /logs`)
* **Execution:** Expand the `GET /logs` endpoint and click **Execute**.
* **Expected Behavior:** The system retrieves the structured log history. 
If executing on a clean database volume, it verifies that the application startup 
lifecycle automatically injected an immutable cryptographically chained 
**Genesis block** anchor utilizing an initial $0^{64}$ previous hash parameter.

#### Test B: Real-time Appendation & Cloud Replication (`POST /logs`)
* **Execution:** Expand the `POST /logs` endpoint, populate the JSON `LogEntry` body
schema with sample data, and click **Execute**:
  ```json
  {
    "source": "AUTH_SERVICE",
    "message": "User admin successfully authenticated from remote host."
  }

Expected Behavior:
1. The API responds with a 201 Created payload status displaying the calculated current block SHA-256 hash value.
2. The console terminal updates with an operational routing event confirmation.
3. The local server file dynamically generates individual compliance blob segments, synchronizing them directly to the remote Azure Storage container as a unique .txt object tracking filename matching the partial block hash.

### Test C: Cryptographic Audit Trail Integrity Engine (GET /logs/verify)

- Execution: Expand the GET /logs/verify endpoint and click Execute.
- Expected Behavior: The cryptographic ledger system triggers a sequential, 
line-by-line verification process. It re-computes and links each block hash to the 
preceding payload parameter to systematically guarantee historical ledger completeness.
The UI should render a clean validation confirmation (200 OK) proving zero data 
modifications or unauthorized structural injections exist.

### Test D: Perimeter Security & WORM Enforcement Check (PUT or DELETE)

- Execution: Attempt to issue any modification or erasure sequence by triggering an active request against either the 
PUT /logs or DELETE /logs routes.
- Expected Behavior: In strict alignment with Write Once, Read Many (WORM) storage standards, the application 
core actively blocks the malicious . The system will aggressively drop the manipulation payload, 
returning a standard security exception response: 403 Forbidden - WORM Policy Violation: Existing logs cannot 
be deleted or modified.

## Clean Shutdown

To exit the runtime environment and stop listening on the network ports, press
Ctrl + C in the primary terminal window. Or execute the following:
```docker-comp down```
