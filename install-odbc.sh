#!/bin/bash

# Install Microsoft ODBC Driver 18 for SQL Server on Railway
echo "Installing Microsoft ODBC Driver 18 for SQL Server..."

# Update package list
apt-get update

# Install required packages
apt-get install -y curl gnupg2 lsb-release

# Add Microsoft's GPG key
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg

# Add Microsoft's repository
echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/ubuntu/$(lsb_release -rs)/prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/mssql-release.list

# Update package list again
apt-get update

# Install ODBC Driver (accept EULA automatically)
ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Install unixODBC development headers
apt-get install -y unixodbc-dev

echo "ODBC Driver installation completed!"
