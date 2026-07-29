#!/bin/bash
# VPS-Specific Update Script for LinkedIn MCP Server
# This script updates the existing installation while preserving Obscura singleton cookies and configuration

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
LINKEDIN_MCP_DIR="${HOME}/.linkedin-mcp"
BACKUP_DIR="${HOME}/.linkedin-mcp-backup-$(date +%Y%m%d-%H%M%S)"
NEW_INSTALL_DIR="${HOME}/.linkedin-mcp/linkedin-cli"

info "Starting LinkedIn MCP Server update..."
info "Backup directory: $BACKUP_DIR"

# Create backup of existing installation
if [ -d "$LINKEDIN_MCP_DIR" ]; then
    info "Creating backup of existing installation..."
    # Create backup directory and copy essential files
    mkdir -p "$BACKUP_DIR"
    
    # Copy important configuration files
    cp -r "$LINKEDIN_MCP_DIR/.env" "$BACKUP_DIR/" 2>/dev/null || true
    cp -r "$LINKEDIN_MCP_DIR/browser-install.json" "$BACKUP_DIR/" 2>/dev/null || true
    cp -r "$LINKEDIN_MCP_DIR/update-check.json" "$BACKUP_DIR/" 2>/dev/null || true
    
    # Copy profile directory (contains Obscura singleton cookies)
    cp -r "$LINKEDIN_MCP_DIR/profile" "$BACKUP_DIR/" 2>/dev/null || true
    
    success "Backup created at $BACKUP_DIR"
fi

# Note: Obscura singleton cookies are already preserved in the profile directory backup

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
    git clone https://github.com/ishan-parihar/linkedin-cli.git "$NEW_INSTALL_DIR"
    cd "$NEW_INSTALL_DIR"
    success "Repository cloned"
fi

# Remove existing profile directory from new installation to avoid conflicts
if [ -d "$NEW_INSTALL_DIR/.linkedin-mcp/profile" ]; then
    info "Removing default profile from new installation..."
    rm -rf "$NEW_INSTALL_DIR/.linkedin-mcp/profile"
fi

# Install dependencies using uv
info "Installing dependencies with uv..."
uv sync

success "Dependencies installed"

# Create symlink for CLI
CLI_PATH="$NEW_INSTALL_DIR/.venv/bin/linkedin-cli"
if [ -f "$CLI_PATH" ]; then
    info "Creating CLI symlink..."
    mkdir -p "$HOME/.local/bin"
    rm -f "$HOME/.local/bin/linkedin-cli"
    ln -s "$CLI_PATH" "$HOME/.local/bin/linkedin-cli"
    success "CLI symlink created"
else
    error "CLI binary not found at $CLI_PATH"
    exit 1
fi

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

# Restore configuration files and profile from backup
if [ -d "$BACKUP_DIR" ]; then
    info "Restoring configuration and profile from backup..."
    
    # Restore configuration files
    cp "$BACKUP_DIR/.env" "$LINKEDIN_MCP_DIR/" 2>/dev/null || true
    cp "$BACKUP_DIR/browser-install.json" "$LINKEDIN_MCP_DIR/" 2>/dev/null || true
    cp "$BACKUP_DIR/update-check.json" "$LINKEDIN_MCP_DIR/" 2>/dev/null || true
    
    # Restore profile directory (contains Obscura singleton cookies)
    if [ -d "$BACKUP_DIR/profile" ]; then
        # Remove existing profile directory if it exists to avoid conflicts
        rm -rf "$LINKEDIN_MCP_DIR/profile" 2>/dev/null || true
        cp -r "$BACKUP_DIR/profile" "$LINKEDIN_MCP_DIR/"
        success "Obscura profile and singleton cookies restored"
    fi
    
    success "Configuration restored from backup"
fi

# Clean up old venv if it exists
if [ -d "${HOME}/.linkedin-mcp-venv" ]; then
    info "Removing old virtual environment..."
    rm -rf "${HOME}/.linkedin-mcp-venv"
    success "Old virtual environment removed"
fi

# Print installation summary
echo ""
success "=========================================="
success "LinkedIn MCP Server Update Complete"
success "=========================================="
echo ""
info "Quick Start:"
echo "  1. Check session status: linkedin-cli status"
echo "  2. Import cookies (if needed): linkedin-cli import [browser]"
echo "  3. Start MCP server: linkedin-cli mcp"
echo ""
info "Backup location: $BACKUP_DIR"
info "For more commands: linkedin-cli --help"
info "Documentation: https://github.com/ishan-parihar/linkedin-cli"
echo ""

success "Update complete!"