#!/bin/bash

# Create a temporary directory for packaging
mkdir -p lambda_package

# Install dependencies into the package directory
pip install -r requirements.txt -t lambda_package/

# Copy your application code
cp -r *.py lambda_package/
cp -r services lambda_package/
cp -r models lambda_package/

# Create the deployment package
cd lambda_package
zip -r ../lambda_deployment.zip .
cd ..

# Clean up
rm -rf lambda_package

echo "Deployment package created: lambda_deployment.zip" 