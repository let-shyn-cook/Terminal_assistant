#!/bin/bash

# Environment Setup Script
# This script creates a .env file if it doesn't exist and prompts for API key

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project directory
cd "$SCRIPT_DIR"

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 AI Agent Environment Setup${NC}"
echo "================================="

# Check if .env file already exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file already exists!${NC}"
    echo ""
    echo "Current contents:"
    echo "----------------"
    cat .env
    echo "----------------"
    echo ""
    
    # Ask if user wants to overwrite
    while true; do
        read -p "Do you want to overwrite the existing .env file? (y/n): " yn
        case $yn in
            [Yy]* ) 
                echo -e "${YELLOW}Backing up existing .env to .env.backup${NC}"
                cp .env .env.backup
                break
                ;;
            [Nn]* ) 
                echo -e "${GREEN}✅ Keeping existing .env file${NC}"
                exit 0
                ;;
            * ) 
                echo "Please answer yes or no."
                ;;
        esac
    done
fi

echo -e "${BLUE}📝 Setting up environment variables...${NC}"
echo ""

# Create .env file
cat > .env << 'EOF'
# AI Agent Environment Variables
GOOGLE_API_KEY=your_api_key_here
EOF

echo -e "${GREEN}✅ Created .env template${NC}"
echo ""

# Function to validate API key format (basic validation)
validate_api_key() {
    local key="$1"
    if [ ${#key} -lt 20 ]; then
        echo -e "${RED}❌ API key seems too short. Please check and try again.${NC}"
        return 1
    fi
    return 0
}

# Get Google API Key
echo -e "${BLUE}🔑 Google Gemini API Key Setup${NC}"
echo "You need a Google Gemini API key to use this AI agent."
echo "Get one at: https://makersuite.google.com/app/apikey"
echo ""

while true; do
    read -s -p "Enter your Google Gemini API key: " GOOGLE_API_KEY
    echo ""
    
    if [ -z "$GOOGLE_API_KEY" ]; then
        echo -e "${RED}❌ API key cannot be empty!${NC}"
        continue
    fi
    
    if validate_api_key "$GOOGLE_API_KEY"; then
        break
    fi
done

# Update the .env file with the actual API key
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/GOOGLE_API_KEY=your_api_key_here/GOOGLE_API_KEY=$GOOGLE_API_KEY/" .env
else
    # Linux
    sed -i "s/GOOGLE_API_KEY=your_api_key_here/GOOGLE_API_KEY=$GOOGLE_API_KEY/" .env
fi

echo -e "${GREEN}✅ Google API key configured${NC}"
echo ""
echo -e "${GREEN}🎉 Environment setup complete!${NC}"
echo ""
echo "Your .env file has been created with the following configuration:"
echo "================================================================="
echo ""

# Display the .env file with sensitive data masked
while IFS= read -r line; do
    if [[ $line == *"API_KEY="* ]] && [[ $line != *"your_"* ]]; then
        # Mask API keys for security
        key_name=$(echo "$line" | cut -d'=' -f1)
        echo "${key_name}=***masked***"
    else
        echo "$line"
    fi
done < .env

echo ""
echo -e "${BLUE}📚 Next steps:${NC}"
echo "1. Run the AI agent with: ./run_agent_pip.sh or ./run_agent_uv.sh"
echo "2. Stop the agent with: ./stop_agent.sh"
echo ""
echo -e "${YELLOW}🔒 Security note: Keep your .env file secure and never commit it to version control!${NC}"
