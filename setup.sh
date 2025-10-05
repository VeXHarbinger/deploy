#!/bin/bash

# Hummingbot Deploy Setup Script
# This script sets up the deployment environment for Hummingbot Deploy
# with all necessary configuration options

set -e  # Exit on any error

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "🚀 Hummingbot Deploy Setup"
echo ""



# Use standalone utils (same logic as utils.py but without Docker dependencies)
export US_DEPLOYMENT=true
CONNECTOR_LIST_US=$(python setup_utils.py get_connector_list)
export US_DEPLOYMENT=false
CONNECTOR_LIST_GLOBAL=$(python setup_utils.py get_connector_list)
DEFAULT_CONNECTOR_ENV=$(python setup_utils.py get_default_connector_name)
CONNECTOR_LIST_TESTS=$(python setup_utils.py get_connector_list_tests)


echo -n "Is this deployment for a US-based user? [y/N][default: N]: "
read IS_US_DEPLOYMENT
IS_US_DEPLOYMENT=$(echo "$IS_US_DEPLOYMENT" | tr '[:upper:]' '[:lower:]')
if [[ "$IS_US_DEPLOYMENT" == "y" || "$IS_US_DEPLOYMENT" == "yes" ]]; then
    IS_US_DEPLOYMENT=true
    CONNECTOR_LIST=$CONNECTOR_LIST_US
    DEFAULT_CONNECTOR="kraken"
else
    IS_US_DEPLOYMENT=false
    CONNECTOR_LIST=$CONNECTOR_LIST_GLOBAL
    DEFAULT_CONNECTOR="$DEFAULT_CONNECTOR_ENV"
fi

# Prompt for test connectors (default: include)
echo -n "Exclude test connectors? [y/N][default: N]: "
read EXCLUDE_TEST_CONNECTORS
EXCLUDE_TEST_CONNECTORS=$(echo "$EXCLUDE_TEST_CONNECTORS" | tr '[:upper:]' '[:lower:]')
if [[ "$EXCLUDE_TEST_CONNECTORS" == "y" || "$EXCLUDE_TEST_CONNECTORS" == "yes" ]]; then
    EXCLUDE_TEST_CONNECTORS=true
    # Do not merge test connectors
else
    EXCLUDE_TEST_CONNECTORS=false
    # Merge test connectors into main connector list (default behavior)
    CONNECTOR_LIST=$(echo $CONNECTOR_LIST | sed 's/^\[//;s/\]$//')
    CONNECTOR_LIST_TESTS_FOR_MERGE=$(echo $CONNECTOR_LIST_TESTS | sed 's/^\[//;s/\]$//')
    CONNECTOR_LIST="[${CONNECTOR_LIST}, ${CONNECTOR_LIST_TESTS_FOR_MERGE}]"
fi

echo -n "Config password [default: admin]: "
read CONFIG_PASSWORD
CONFIG_PASSWORD=${CONFIG_PASSWORD:-admin}

echo -n "Dashboard username [default: admin]: "
read USERNAME
USERNAME=${USERNAME:-admin}

echo -n "Dashboard password [default: admin]: "
read PASSWORD
PASSWORD=${PASSWORD:-admin}

# Set paths and defaults
BOTS_PATH=$(pwd)

# Use sensible defaults for deployment
DEBUG_MODE="false"
BROKER_HOST="localhost"
BROKER_PORT="1883"
BROKER_USERNAME="admin"
BROKER_PASSWORD="password"
DATABASE_URL="postgresql+asyncpg://hbot:hummingbot-api@localhost:5432/hummingbot_api"
CLEANUP_INTERVAL="300"
FEED_TIMEOUT="600"
AWS_API_KEY=""
AWS_SECRET_KEY=""
S3_BUCKET=""
LOGFIRE_ENV="prod"
BANNED_TOKENS='["NAV","ARS","ETHW","ETHF","NEWT"]'

echo ""

echo -e "${GREEN}📦 Installing Python dependencies from requirements.txt...${NC}"
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Python dependencies installed!${NC}"
else
    echo -e "${YELLOW}⚠️ requirements.txt not found. Please install dependencies manually if needed.${NC}"
fi

echo -e "${GREEN}✅ Using sensible defaults for MQTT, Database, and other settings${NC}"

echo ""
echo -e "${GREEN}📝 Creating .env file...${NC}"

# Create .env file with proper structure and comments

# Set API URL and PORT for dashboard/trading
BACKEND_API_URL=localhost
BACKEND_API_PORT=8000

cat > .env << EOF
# =================================================================
# Hummingbot Deploy Environment Configuration
# Generated on: $(date)
# =================================================================

# =================================================================
# 🌎 Deployment Region
# =================================================================
US_DEPLOYMENT=$IS_US_DEPLOYMENT
EXCLUDE_TEST_CONNECTORS=$EXCLUDE_TEST_CONNECTORS

# =================================================================
# 🔐 Security Configuration
# =================================================================
USERNAME=$USERNAME
PASSWORD=$PASSWORD
DEBUG_MODE=$DEBUG_MODE
CONFIG_PASSWORD=$CONFIG_PASSWORD

# =================================================================
# 🔗 MQTT Broker Configuration (BROKER_*)
# =================================================================
BROKER_HOST=$BROKER_HOST
BROKER_PORT=$BROKER_PORT
BROKER_USERNAME=$BROKER_USERNAME
BROKER_PASSWORD=$BROKER_PASSWORD

# =================================================================
# 💾 Database Configuration (DATABASE_*)
# =================================================================
DATABASE_URL=$DATABASE_URL

# =================================================================
# 📊 Market Data Feed Manager Configuration (MARKET_DATA_*)
# =================================================================
MARKET_DATA_CLEANUP_INTERVAL=$CLEANUP_INTERVAL
MARKET_DATA_FEED_TIMEOUT=$FEED_TIMEOUT

# =================================================================
# ☁️ AWS Configuration (AWS_*) - Optional
# =================================================================
AWS_API_KEY=$AWS_API_KEY
AWS_SECRET_KEY=$AWS_SECRET_KEY
AWS_S3_DEFAULT_BUCKET_NAME=$S3_BUCKET

# =================================================================
# ⚙️ Application Settings
# =================================================================
LOGFIRE_ENVIRONMENT=$LOGFIRE_ENV
BANNED_TOKENS=$BANNED_TOKENS

# =================================================================
# 📁 Application Paths
# =================================================================
BOTS_PATH=$BOTS_PATH

# =================================================================
# 🔗 Connector Lists
# =================================================================
CONNECTOR_LIST_US=$CONNECTOR_LIST_US
CONNECTOR_LIST_GLOBAL=$CONNECTOR_LIST_GLOBAL
CONNECTOR_LIST_TESTS=$CONNECTOR_LIST_TESTS
DEFAULT_CONNECTOR=$DEFAULT_CONNECTOR
AVAILABLE_CONNECTORS=$CONNECTOR_LIST

EOF

echo -e "${GREEN}✅ .env file created successfully!${NC}"
echo ""

# Display configuration summary
echo -e "${BLUE}📋 Configuration Summary${NC}"
echo "======================="
echo -e "${CYAN}Security:${NC} Username: $USERNAME, Debug: $DEBUG_MODE"
echo -e "${CYAN}Broker:${NC} $BROKER_HOST:$BROKER_PORT"
echo -e "${CYAN}Database:${NC} ${DATABASE_URL%%@*}@[hidden]"
echo -e "${CYAN}Market Data:${NC} Cleanup: ${CLEANUP_INTERVAL}s, Timeout: ${FEED_TIMEOUT}s"
echo -e "${CYAN}Environment:${NC} $LOGFIRE_ENV"

if [ -n "$AWS_API_KEY" ]; then
    echo -e "${CYAN}AWS:${NC} Configured with S3 bucket: $S3_BUCKET"
else
    echo -e "${CYAN}AWS:${NC} Not configured (optional)"
fi

echo ""
echo -e "${GREEN}🐳 Pulling required Docker images...${NC}"

# Pull Docker images in parallel
docker compose pull &
docker pull hummingbot/hummingbot:latest &

# Wait for both operations to complete
wait

echo -e "${GREEN}✅ All Docker images pulled successfully!${NC}"
echo ""

# Check if password verification file exists
if [ ! -f "bots/credentials/master_account/.password_verification" ]; then
    echo -e "${YELLOW}📌 Note:${NC} Password verification file will be created on first startup"
    echo -e "   Location: ${BLUE}bots/credentials/master_account/.password_verification${NC}"
    echo ""
fi

echo -e "${GREEN}🚀 Starting Hummingbot Deploy services...${NC}"

# Start the deployment
docker compose up -d

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""

echo -e "Your services are now running:"
echo -e "📊 ${BLUE}Dashboard:${NC} http://localhost:8501"
echo -e "🔧 ${BLUE}API Docs:${NC} http://localhost:8000/docs"
echo -e "📡 ${BLUE}MQTT Broker:${NC} localhost:1883"
echo ""

echo -e "Next steps:"
echo "1. Access the Dashboard: http://localhost:8501"
echo "2. Configure your trading strategies"
echo "3. Monitor logs: docker compose logs -f"
echo ""
echo -e "${PURPLE}💡 Pro tip:${NC} You can modify environment variables in .env file anytime"
echo -e "${PURPLE}📚 Documentation:${NC} Check CLAUDE.md for project guidance"
echo -e "${PURPLE}🔒 Security:${NC} The password verification file secures bot credentials"
echo ""
echo -e "${GREEN}Happy Trading! 🤖💰${NC}"
