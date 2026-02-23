#!/bin/bash

# Configuration
FUNCTION_NAME="brand-insights-fetcher"
S3_BUCKET="brand-insights-bucket"
REGION="us-east-1"
ROLE_ARN="arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role"  # Replace with your role

echo "🚀 Deploying Brand Insights Lambda Function..."

# Create deployment package
echo "📦 Creating deployment package..."
rm -rf package
mkdir package

# Install dependencies
pip install -r requirements.txt -t package/

# Copy function code
cp lambda_function.py auth_handler.py package/

# Zip everything
cd package
zip -r ../function.zip .
cd ..

# Update or create Lambda function
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "🔄 Updating existing function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://function.zip \
        --region $REGION
else
    echo "✨ Creating new function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://function.zip \
        --timeout 300 \
        --memory-size 2048 \
        --environment Variables={S3_BUCKET_NAME=$S3_BUCKET} \
        --region $REGION
fi

# Clean up
rm -rf package function.zip

echo "✅ Deployment complete!"