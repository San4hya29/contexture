#!/bin/bash
# run_all.sh - Start all services (Docker containers and application components)
# Usage: ./run_all.sh
# Compatible with: Linux, macOS, Windows (WSL/Git Bash), and BSD

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo -e "${CYAN}Starting SODA Contexture services...${NC}"
echo -e "${CYAN}Project root: $PROJECT_ROOT${NC}"

# ============================================================================
# Detect OS and terminal
# ============================================================================
OS_TYPE=$(uname -s)
IS_WINDOWS=false
TERMINAL_CMD=""

if [[ "$OS_TYPE" == "MINGW64"* ]] || [[ "$OS_TYPE" == "MSYS"* ]] || [[ "$OSTYPE" == "msys" ]]; then
    IS_WINDOWS=true
    TERMINAL_CMD="cmd.exe /c start"
elif [[ "$OS_TYPE" == "Darwin" ]]; then
    # macOS
    TERMINAL_CMD="open -a Terminal.app"
elif [[ "$OS_TYPE" == "Linux" ]]; then
    # Linux - try common terminal emulators
    if command -v gnome-terminal &> /dev/null; then
        TERMINAL_CMD="gnome-terminal --"
    elif command -v konsole &> /dev/null; then
        TERMINAL_CMD="konsole -e"
    elif command -v xterm &> /dev/null; then
        TERMINAL_CMD="xterm -e"
    else
        echo -e "${YELLOW}Warning: No standard terminal emulator found. Using xterm as fallback.${NC}"
        TERMINAL_CMD="xterm -e"
    fi
fi

# ============================================================================
# 1. Start Docker Containers
# ============================================================================
echo -e "\n${YELLOW}[1/5] Cleaning up existing containers...${NC}"

docker ps -a -q --filter "name=prometheus" 2>/dev/null | xargs -r docker stop 2>/dev/null | xargs -r docker rm 2>/dev/null
docker ps -a -q --filter "name=mongodb" 2>/dev/null | xargs -r docker stop 2>/dev/null | xargs -r docker rm 2>/dev/null
sleep 2

echo -e "\n${YELLOW}[2/5] Starting Prometheus container...${NC}"

docker run \
  -d \
  --name prometheus \
  -p 9090:9090 \
  -v "${PROJECT_ROOT}/config/prometheus_run_config.yaml:/etc/prometheus/prometheus.yml" \
  prom/prometheus:latest \
  --config.file=/etc/prometheus/prometheus.yml \
  --web.enable-remote-write-receiver > /dev/null

echo -e "${GREEN}Prometheus container started (accessible at http://localhost:9090)${NC}"

echo -e "\n${YELLOW}[3/5] Starting MongoDB container...${NC}"

docker run \
  -d \
  --name mongodb \
  -e MONGO_INITDB_DATABASE=ocs \
  -p 27017:27017 \
  mongo:6 > /dev/null

echo -e "${GREEN}MongoDB container started (accessible at localhost:27017)${NC}"

echo -e "\n${YELLOW}[3/5] Waiting for services to be ready...${NC}"
sleep 3

# ============================================================================
# 2. Open Terminal Windows for Application Components
# ============================================================================
echo -e "\n${YELLOW}[4/5] Opening terminal tabs...${NC}"

if [ "$IS_WINDOWS" = true ]; then
    # Windows CMD approach
    echo -e "${CYAN}  - Tab 1: OCS Server (go run ./pkg/ocs/)${NC}"
    cmd.exe /c start "OCS Server" /D "$PROJECT_ROOT" powershell -NoExit -Command "go run ./pkg/ocs/"
    
    echo -e "${CYAN}  - Tab 2: Prometheus Data Pusher${NC}"
    cmd.exe /c start "Prometheus Data Pusher" /D "$PROJECT_ROOT\pkg\utils" powershell -NoExit -Command "python prometheus_data_pusher.py --config config.json"
    
    echo -e "${CYAN}  - Tab 3: FastMCP Server${NC}"
    cmd.exe /c start "FastMCP Server" /D "$PROJECT_ROOT\pkg\mcp" powershell -NoExit -Command "fastmcp run server.py:app --transport http --port 8001"
    
    echo -e "${CYAN}  - Tab 4: MCP Client${NC}"
    cmd.exe /c start "MCP Client" /D "$PROJECT_ROOT\pkg\mcp" powershell -NoExit -Command "python client_dynamic.py"

elif [[ "$OS_TYPE" == "Darwin" ]]; then
    # macOS - use open command with Bash
    echo -e "${CYAN}  - Tab 1: OCS Server (go run ./pkg/ocs/)${NC}"
    open -a Terminal "$SCRIPT_DIR/terminal_tab.sh" "OCS Server" "cd '$PROJECT_ROOT' && go run ./pkg/ocs/"
    
    echo -e "${CYAN}  - Tab 2: Prometheus Data Pusher${NC}"
    open -a Terminal "$SCRIPT_DIR/terminal_tab.sh" "Prometheus Data Pusher" "cd '$PROJECT_ROOT/pkg/utils' && python prometheus_data_pusher.py --config config.json"
    
    echo -e "${CYAN}  - Tab 3: FastMCP Server${NC}"
    open -a Terminal "$SCRIPT_DIR/terminal_tab.sh" "FastMCP Server" "cd '$PROJECT_ROOT/pkg/mcp' && fastmcp run server.py:app --transport http --port 8001"
    
    echo -e "${CYAN}  - Tab 4: MCP Client${NC}"
    open -a Terminal "$SCRIPT_DIR/terminal_tab.sh" "MCP Client" "cd '$PROJECT_ROOT/pkg/mcp' && python client_dynamic.py"

else
    # Linux and other Unix-like systems
    echo -e "${CYAN}  - Tab 1: OCS Server (go run ./pkg/ocs/)${NC}"
    new_terminal_window "OCS Server" "cd '$PROJECT_ROOT' && go run ./pkg/ocs/"
    
    echo -e "${CYAN}  - Tab 2: Prometheus Data Pusher${NC}"
    new_terminal_window "Prometheus Data Pusher" "cd '$PROJECT_ROOT/pkg/utils' && python prometheus_data_pusher.py --config config.json"
    
    echo -e "${CYAN}  - Tab 3: FastMCP Server${NC}"
    new_terminal_window "FastMCP Server" "cd '$PROJECT_ROOT/pkg/mcp' && fastmcp run server.py:app --transport http --port 8001"
    
    echo -e "${CYAN}  - Tab 4: MCP Client${NC}"
    new_terminal_window "MCP Client" "cd '$PROJECT_ROOT/pkg/mcp' && python client_dynamic.py"
fi

# ============================================================================
# 3. Status Summary
# ============================================================================
echo -e "\n${GREEN}[5/5] All services started!${NC}"
echo -e "\n$(printf '=%.0s' {1..70})"
echo -e "${CYAN}SERVICE STATUS:${NC}"
echo -e "$(printf '=%.0s' {1..70})"

echo -e "\n${YELLOW}[DOCKER CONTAINERS]${NC}"
echo -e "${GREEN}  • Prometheus:  http://localhost:9090${NC}"
echo -e "${GREEN}  • MongoDB:     localhost:27017${NC}"

echo -e "\n${YELLOW}[TERMINAL TABS]${NC}"
echo -e "${GREEN}  • Tab 1: OCS Server (Go)${NC}"
echo -e "${GREEN}  • Tab 2: Prometheus Data Pusher (Python)${NC}"
echo -e "${GREEN}  • Tab 3: FastMCP Server (Python) - http://localhost:8001${NC}"
echo -e "${GREEN}  • Tab 4: MCP Client (Python)${NC}"

echo -e "\n$(printf '=%.0s' {1..70})"
echo -e "${YELLOW}STOPPING ALL SERVICES:${NC}"
echo -e "${CYAN}  • Run: ./stop_all.sh${NC}"
echo -e "${CYAN}  • Or manually run: docker stop prometheus-contexture mongodb-contexture${NC}"
echo -e "$(printf '=%.0s' {1..70})"
echo ""

# Helper function to open new terminal window on Linux
new_terminal_window() {
    local title="$1"
    local cmd="$2"
    
    if [[ "$TERMINAL_CMD" =~ "gnome-terminal" ]]; then
        gnome-terminal -- bash -c "$cmd; exec bash" &
    elif [[ "$TERMINAL_CMD" =~ "konsole" ]]; then
        konsole -e bash -c "$cmd; exec bash" &
    elif [[ "$TERMINAL_CMD" =~ "xterm" ]]; then
        xterm -T "$title" -e bash -c "$cmd; exec bash" &
    else
        # Fallback: run in background
        bash -c "$cmd" &
    fi
}
