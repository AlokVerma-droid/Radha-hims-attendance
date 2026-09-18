#!/usr/bin/env bash
# Exit on error
set -o errexit

# Microsoft repository keys add karein
apt-get update && apt-get install -y curl gnupg
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Package list update karke ODBC Driver 17 install karein
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

# Python packages install karein
pip install -r requirements.txt