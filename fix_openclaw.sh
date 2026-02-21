#!/bin/bash
# Fix OpenClaw installation - resolve Node.js upgrade conflict

echo "🔧 Fixing OpenClaw installation..."
echo ""

echo "Step 1: Removing conflicting packages"
sudo apt-get remove -y libnode-dev libnode72 nodejs-doc

echo ""
echo "Step 2: Cleaning up package manager"
sudo apt-get autoremove -y
sudo apt-get clean
sudo dpkg --configure -a

echo ""
echo "Step 3: Installing Node.js v22 from NodeSource"
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

echo ""
echo "Step 4: Verifying Node.js installation"
node --version
npm --version

echo ""
echo "Step 5: Installing OpenClaw"
curl -fsSL https://openclaw.ai/install.sh | bash

echo ""
echo "✅ Installation complete!"
