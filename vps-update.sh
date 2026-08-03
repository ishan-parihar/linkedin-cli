#!/bin/bash
# VPS Update Script for LinkedIn MCP Server
# This script updates the existing installation while preserving cookies and configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Set paths
LINKEDIN_MCP_DIR="${HOME}/.linkedin"
BACKUP_DIR="${HOME}/.linkedin-backup-$(date +%Y%m%d-%H%M%S)"
NEW_INSTALL_DIR="${HOME}/.linkedin/linkedin-lyr"

info "Starting LinkedIn MCP Server update..."
info "Backup directory: $BACKUP_DIR"

# Create backup of existing installation
if [ -d "$LINKEDIN_MCP_DIR" ]; then
    info "Creating backup of existing installation..."
    cp -r "$LINKEDIN_MCP_DIR" "$BACKUP_DIR"
    success "Backup created at $BACKUP_DIR"
fi

# Preserve existing cookies if they exist
COOKIES_BACKUP=""
if [ -f "$LINKEDIN_MCP_DIR/cookies.json" ]; then
    info "Preserving existing cookies..."
    COOKIES_BACKUP="/tmp/linkedin-cookies-$(date +%Y%m%d-%H%M%S).json"
    cp "$LINKEDIN_MCP_DIR/cookies.json" "$COOKIES_BACKUP"
    success "Cookies backed up to $COOKIES_BACKUP"
fi

# Preserve browser profile if it exists
PROFILE_BACKUP=""
if [ -d "$LINKEDIN_MCP_DIR/profile" ]; then
    info "Preserving browser profile..."
    PROFILE_BACKUP="/tmp/linkedin-profile-$(date +%Y%m%d-%H%M%S)"
    cp -r "$LINKEDIN_MCP_DIR/profile" "$PROFILE_BACKUP"
    success "Browser profile backed up to $PROFILE_BACKUP"
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    info "uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    success "uv installed successfully"
else
    success "uv is already installed: $(uv --version)"
fi

# Create installation directory
mkdir -p "$LINKEDIN_MCP_DIR"

# Clone or update repository
if [ -d "$NEW_INSTALL_DIR" ]; then
    info "Repository already exists. Updating..."
    cd "$NEW_INSTALL_DIR"
    git fetch origin
    git reset --hard origin/main
    success "Repository updated"
else
    info "Cloning repository..."
    git clone https://github.com/ishan-parihar/linkedin-lyr.git "$NEW_INSTALL_DIR"
    cd "$NEW_INSTALL_DIR"
    success "Repository cloned"
fi

# Install dependencies using uv
info "Installing dependencies with uv..."
uv sync

success "Dependencies installed"

# Create symlink for CLI
info "Creating CLI symlink..."
mkdir -p "$HOME/.local/bin"
rm -f "$HOME/.local/bin/linkedin-lyr"
ln -s "$NEW_INSTALL_DIR/.venv/bin/linkedin-lyr" "$HOME/.local/bin/linkedin-lyr"
success "CLI symlink created"

# Ensure PATH includes ~/.local/bin
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    warning "$HOME/.local/bin is not in PATH. Adding to shell profile..."
    
    # Detect shell and add to appropriate profile
    SHELL_RC=""
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        SHELL_RC="$HOME/.bashrc"
    else
        SHELL_RC="$HOME/.profile"
    fi
    
    if ! grep -q "linkedin-mcp" "$SHELL_RC"; then
        echo "" >> "$SHELL_RC"
        echo "# LinkedIn MCP Server" >> "$SHELL_RC"
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$SHELL_RC"
        success "Added to $SHELL_RC. Please run: source $SHELL_RC"
    fi
fi

# Restore cookies if they were backed up
if [ -n "$COOKIES_BACKUP" ] && [ -f "$COOKIES_BACKUP" ]; then
    info "Restoring cookies..."
    cp "$COOKIES_BACKUP" "$LINKEDIN_MCP_DIR/cookies.json"
    chmod 600 "$LINKEDIN_MCP_DIR/cookies.json"
    success "Cookies restored"
fi

# Restore browser profile if it was backed up
if [ -n "$PROFILE_BACKUP" ] && [ -d "$PROFILE_BACKUP" ]; then
    info "Restoring browser profile..."
    cp -r "$PROFILE_BACKUP" "$LINKEDIN_MCP_DIR/profile"
    success "Browser profile restored"
fi

# Clean up old venv if it exists
if [ -d "${HOME}/.linkedin-venv" ]; then
    info "Removing old virtual environment..."
    rm -rf "${HOME}/.linkedin-venv"
    success "Old virtual environment removed"
fi

# Print installation summary
echo ""
success "=========================================="
success "LinkedIn MCP Server Update Complete"
success "=========================================="
echo ""
info "Quick Start:"
echo "  1. Check session status: linkedin-lyr status"
echo "  2. Import cookies (if needed): linkedin-lyr import [browser]"
echo "  3. Start MCP server: linkedin-lyr mcp"
echo ""
info "Backup location: $BACKUP_DIR"
info "For more commands: linkedin-lyr --help"
info "Documentation: https://github.com/ishan-parihar/linkedin-lyr"
echo ""

success "Update complete!"