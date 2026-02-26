#!/bin/bash

# Configuration
FUNCTION_NAME="brand-insights-fetcher"
REGION="us-east-1"
ROLE_ARN="arn:aws:iam::629061775535:role/brand-insights-lambda-role"

echo " Deploying Brand Insights Lambda Function..."

# Create deployment package
echo " Creating deployment package..."
rm -rf package
mkdir package

# Install dependencies (playwright-core only - much smaller!)
echo " Installing dependencies..."
pip install -r requirements.txt -t package/

# Copy function code
echo " Copying function code..."
cp lambda_function.py auth_handler.py package/

# Create zip
echo " Creating zip file..."
cd package
zip -r ../function.zip .
cd ..

# Check zip size - should be MUCH smaller now!
ZIP_SIZE=$(du -h function.zip | cut -f1)
echo " Zip file created: $ZIP_SIZE (should be <10MB)"

# Set environment variables for Chromium download
ENV_VARS="Variables={"
ENV_VARS+="PLAYWRIGHT_CHROMIUM_DOWNLOAD_HOST=https://files.chromiumforlambda.org/amazon-linux-2/x86_64,"
ENV_VARS+="PLAYWRIGHT_BROWSERS_PATH=/tmp"
ENV_VARS+="}"

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo " Updating existing function..."
    
    # Update code
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://function.zip \
        --region $REGION
    
    # Update configuration with environment variables
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --timeout 300 \
        --memory-size 2048 \
        --environment "$ENV_VARS" \
        --region $REGION
        
    echo " Update complete!"
else
    echo " Creating new function..."
    
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime python3.11 \
        --role "$ROLE_ARN" \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://function.zip \
        --timeout 300 \
        --memory-size 2048 \
        --environment "$ENV_VARS" \
        --region "$REGION"
        
    if [ $? -eq 0 ]; then
        echo " Function created successfully!"
    else
        echo " Creation failed!"
        exit 1
    fi
fi

# Optional clean up
echo ""
read -p "🧹 Delete temporary files? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf package function.zip
    echo " Cleanup complete"
fi

echo ""
echo " =========================================="
echo " DEPLOYMENT COMPLETE!"
echo " =========================================="
echo ""
echo " Test with:"
echo "aws lambda invoke --function-name $FUNCTION_NAME --payload file://event.json response.json && cat response.json"