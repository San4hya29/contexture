#!/bin/bash
# stop_all.sh - Stop all services (Docker containers and applications)
# Usage: ./stop_all.sh
# Compatible with: Linux, macOS, Windows (WSL/Git Bash), and BSD

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}Stopping SODA Contexture services...${NC}"

echo -e "\n${YELLOW}Stopping Docker containers...${NC}"

containers=("prometheus" "mongodb")

for container in "${containers[@]}"; do
    echo -e "${CYAN}  Stopping $container...${NC}"
    docker stop "$container" 2>/dev/null || true
    docker rm "$container" 2>/dev/null || true
done

echo -e "\n${GREEN}Docker containers stopped.${NC}"
echo -e "${CYAN}Note: Terminal tabs remain open. Close them manually or type 'exit'${NC}"
echo ""
