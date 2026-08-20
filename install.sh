#!/bin/bash
# ================================================================
# Server Manager Backend - Complete Installation Script
# ================================================================
# This script installs all host prerequisites and launches the
# entire stack on a fresh Linux OS (Ubuntu/Debian or RHEL/CentOS).
# ================================================================

set -e  # Exit on any error

# Colors for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ================================================================
# 1. Detect OS
# ================================================================
detect_os() {
    echo -e "${BLUE}🔍 Detecting Operating System...${NC}"
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
        echo -e "${GREEN}✅ Detected: $OS $VERSION${NC}"
    else
        echo -e "${RED}❌ Cannot detect OS. Exiting.${NC}"
        exit 1
    fi
}

# ================================================================
# 2. Install Docker Engine & Compose
# ================================================================
install_docker() {
    echo -e "${BLUE}🐳 Installing Docker Engine...${NC}"

    case $OS in
        ubuntu|debian)
            # Remove old versions
            sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

            # Install prerequisites
            sudo apt-get update
            sudo apt-get install -y \
                ca-certificates \
                curl \
                gnupg \
                lsb-release

            # Add Docker's official GPG key
            sudo mkdir -p /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/$OS/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

            # Set up the repository
            echo \
              "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS \
              $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

            # Install Docker Engine
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

            # Add user to docker group
            sudo usermod -aG docker $USER
            echo -e "${GREEN}✅ Docker installed successfully.${NC}"
            ;;

        rhel|centos|fedora|rocky|almalinux)
            # Remove old versions
            sudo dnf remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine 2>/dev/null || true

            # Install prerequisites
            sudo dnf install -y dnf-utils

            # Add Docker repository
            sudo dnf config-manager --add-repo https://download.docker.com/linux/$OS/docker-ce.repo

            # Install Docker Engine
            sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

            # Start Docker service
            sudo systemctl start docker
            sudo systemctl enable docker

            # Add user to docker group
            sudo usermod -aG docker $USER
            echo -e "${GREEN}✅ Docker installed successfully.${NC}"
            ;;

        *)
            echo -e "${RED}❌ Unsupported OS: $OS${NC}"
            exit 1
            ;;
    esac
}

# ================================================================
# 3. Install Git
# ================================================================
install_git() {
    echo -e "${BLUE}📦 Installing Git...${NC}"
    case $OS in
        ubuntu|debian)
            sudo apt-get install -y git
            ;;
        rhel|centos|fedora|rocky|almalinux)
            sudo dnf install -y git
            ;;
    esac
    echo -e "${GREEN}✅ Git installed.${NC}"
}

# ================================================================
# 4. Install OpenSSL (for generating secrets)
# ================================================================
install_openssl() {
    echo -e "${BLUE}🔐 Installing OpenSSL...${NC}"
    case $OS in
        ubuntu|debian)
            sudo apt-get install -y openssl
            ;;
        rhel|centos|fedora|rocky|almalinux)
            sudo dnf install -y openssl
            ;;
    esac
    echo -e "${GREEN}✅ OpenSSL installed.${NC}"
}

# ================================================================
# 5. Create Required Directories
# ================================================================
create_directories() {
    echo -e "${BLUE}📁 Creating required directories...${NC}"
    
    # Prometheus targets directory
    mkdir -p ./prometheus_targets
    chmod 755 ./prometheus_targets
    
    # Backup directories (optional)
    sudo mkdir -p /backup/oracle /backup/mssql
    sudo chmod 755 /backup/oracle /backup/mssql
    
    # SSL directory (if not exists)
    sudo mkdir -p /etc/letsencrypt
    
    echo -e "${GREEN}✅ Directories created.${NC}"
}

# ================================================================
# 6. Generate .env File (If Not Exists)
# ================================================================
generate_env() {
    if [ ! -f .env ]; then
        echo -e "${BLUE}📝 Generating .env file...${NC}"
        
        cat > .env << EOF
# ================================================================
# Server Manager Backend - Environment Configuration
# ================================================================

# ----- Core Security (Required) -----
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ----- Admin User (Required for first run) -----
FIRST_SUPERUSER=admin
FIRST_SUPERUSER_PASSWORD=$(openssl rand -hex 12)

# ----- Database -----
DATABASE_URL=sqlite+aiosqlite:///./server_manager.db

# ----- CORS (Frontend Access) -----
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# ----- Grafana Dashboard -----
GRAFANA_PASSWORD=$(openssl rand -hex 8)

# ----- File Browser Base Directory (Optional) -----
# FILE_BROWSER_BASE_DIR=/home/admin

EOF
        
        echo -e "${GREEN}✅ .env file created.${NC}"
        echo -e "${YELLOW}⚠️  IMPORTANT: Save these credentials:${NC}"
        echo -e "   Admin Username: admin"
        echo -e "   Admin Password: $(grep FIRST_SUPERUSER_PASSWORD .env | cut -d '=' -f2)"
        echo -e "   Grafana Password: $(grep GRAFANA_PASSWORD .env | cut -d '=' -f2)"
        echo -e "   SECRET_KEY: $(grep SECRET_KEY .env | cut -d '=' -f2)"
    else
        echo -e "${YELLOW}⚠️  .env file already exists. Skipping generation.${NC}"
    fi
}

# ================================================================
# 7. Sudoers Configuration for Oracle (Optional)
# ================================================================
configure_sudoers() {
    echo -e "${BLUE}🔧 Configuring sudoers for Oracle (optional)...${NC}"
    
    if [ -d "/u01/app/oracle/product" ] || [ -d "/u02/app/oracle/product" ] || [ -d "/opt/oracle/product" ]; then
        echo -e "${YELLOW}⚠️  Oracle directories detected. Setting up sudoers...${NC}"
        
        sudo tee /etc/sudoers.d/oracle > /dev/null << 'EOF'
# Allow Docker user to run Oracle commands as oracle user without password
root ALL=(oracle) NOPASSWD: /u01/app/oracle/product/*/bin/dbstart, /u01/app/oracle/product/*/bin/dbshut, /u01/app/oracle/product/*/bin/rman, /u01/app/oracle/product/*/bin/expdp, /u01/app/oracle/product/*/bin/impdp, /u01/app/oracle/product/*/bin/dbca
EOF
        sudo chmod 440 /etc/sudoers.d/oracle
        echo -e "${GREEN}✅ Sudoers configured.${NC}"
    else
        echo -e "${YELLOW}⚠️  No Oracle directories found. Skipping sudoers configuration.${NC}"
        echo -e "   If you plan to use Oracle features, install Oracle first."
    fi
}

# ================================================================
# 8. Launch the Stack
# ================================================================
launch_stack() {
    echo -e "${BLUE}🚀 Launching the stack...${NC}"
    
    # Determine which compose file to use
    if [ -f docker-compose.ubuntu.yml ]; then
        COMPOSE_FILE="docker-compose.ubuntu.yml"
    elif [ -f docker-compose.rhel.yml ]; then
        COMPOSE_FILE="docker-compose.rhel.yml"
    else
        COMPOSE_FILE="docker-compose.yml"
    fi
    
    echo -e "${BLUE}Using compose file: $COMPOSE_FILE${NC}"
    
    # Build and start the stack
    docker compose -f $COMPOSE_FILE up --build -d
    
    echo -e "${GREEN}✅ Stack launched successfully!${NC}"
}

# ================================================================
# 9. Show Access Information
# ================================================================
show_info() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ Installation Complete! Access your services:${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}📡 API & Management:${NC}"
    echo -e "   🔗 API Documentation:   http://localhost:8000/docs"
    echo -e "   🔗 API Root:            http://localhost:8000/"
    echo -e "   🔗 Health Check:        http://localhost:8000/health"
    echo ""
    echo -e "${BLUE}📊 Observability:${NC}"
    echo -e "   📈 Grafana Dashboard:   http://localhost:3000"
    echo -e "      Username: admin"
    echo -e "      Password: $(grep GRAFANA_PASSWORD .env | cut -d '=' -f2 2>/dev/null || echo 'see .env file')"
    echo -e "   📊 Prometheus:          http://localhost:9090"
    echo -e "   📋 Loki:                http://localhost:3100"
    echo ""
    echo -e "${BLUE}🔐 Admin Credentials:${NC}"
    echo -e "   Username: admin"
    echo -e "   Password: $(grep FIRST_SUPERUSER_PASSWORD .env | cut -d '=' -f2 2>/dev/null || echo 'see .env file')"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT: Save these credentials! They are also stored in .env${NC}"
    echo ""
    echo -e "${BLUE}🛠️  Useful Commands:${NC}"
    echo -e "   docker compose -f $COMPOSE_FILE ps          # Check service status"
    echo -e "   docker compose -f $COMPOSE_FILE logs        # View logs"
    echo -e "   docker compose -f $COMPOSE_FILE down        # Stop all services"
    echo -e "   docker compose -f $COMPOSE_FILE up -d       # Start services"
    echo ""
    echo -e "${GREEN}🎯 All services are running!${NC}"
}

# ================================================================
# 10. Main Execution
# ================================================================
main() {
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Server Manager Backend - Complete Installation Script  ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    # Check if running as root (we need sudo)
    if [ "$EUID" -eq 0 ]; then
        echo -e "${RED}❌ Please run this script as a regular user (not root).${NC}"
        echo -e "   It will use sudo when needed."
        exit 1
    fi

    # Detect OS
    detect_os

    # Install prerequisites
    install_docker
    install_git
    install_openssl

    # Create directories
    create_directories

    # Generate .env
    generate_env

    # Configure sudoers (optional)
    configure_sudoers

    # Launch the stack
    launch_stack

    # Show access information
    show_info

    echo -e "${GREEN}🎉 All done! Enjoy your Enterprise Linux Management Suite.${NC}"
}

# ================================================================
# Run the main function
# ================================================================
main "$@"
