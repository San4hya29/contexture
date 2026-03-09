# Test Scripts

## Service Orchestration

### Platform-Specific Scripts

Choose the script appropriate for your shell/terminal:

#### **Windows (PowerShell)**
```powershell
./run_all.ps1    # Start all services
./stop_all.ps1   # Stop all services
```

#### **Windows (CMD)**
```cmd
run_all.bat      # Start all services
stop_all.bat     # Stop all services
```

#### **Linux, macOS, WSL, Git Bash**
```bash
./run_all.sh     # Start all services
./stop_all.sh    # Stop all services
```

### What the Scripts Do

All scripts start the same services in parallel:

1. **Prometheus Docker container** (port 9090)
2. **MongoDB Docker container** (port 27017)
3. **4 separate terminal windows** for:
   - **Tab/Window 1**: OCS Server (`go run ./pkg/ocs/`)
   - **Tab/Window 2**: Prometheus Data Pusher (`python prometheus_data_pusher.py --config config.json`)
   - **Tab/Window 3**: FastMCP Server (`fastmcp run server.py:app --transport http --port 8001`)
   - **Tab/Window 4**: MCP Client (`python client_dynamic.py`)

### Prerequisites

- Docker Desktop running
- Python 3.x configured (with dependencies installed)
- Go configured
- FastMCP installed (`pip install fastmcp`)

### Stop Services

To stop all services, run the corresponding stop script for your platform:

```powershell
# PowerShell
./stop_all.ps1
```

```cmd
# Windows CMD
stop_all.bat
```

```bash
# Bash (Linux/macOS/WSL)
./stop_all.sh
```

Or manually: `docker stop prometheus-contexture mongodb-contexture`

---

## Service Endpoints

Once running, the following services are available:

| Service | Location | Details |
|---------|----------|---------|
| Prometheus | http://localhost:9090 | Metrics and monitoring |
| MongoDB | localhost:27017 | Database (MONGO_INITDB_DATABASE=ocs) |
| FastMCP Server | http://localhost:8001 | Model Context Protocol server |
| OCS Server | Logs in Tab 1 | OpenContainer System server |

---

## Query Test Sets

Sample query files are available in this directory:
- `example1.yaml` - Sample query set 1
- `example2.yaml` - Sample query set 2

Run queries against the OCS server using these configurations.
