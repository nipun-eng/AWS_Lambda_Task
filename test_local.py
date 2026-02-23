import json
import os
from lambda_function import lambda_handler

# Mock event for testing
test_event = {
    'urls': [
        'https://www.instagram.com/nike',
        'https://twitter.com/nike'
    ]
}

# Set environment variable for local testing
os.environ['S3_BUCKET_NAME'] = 'test-bucket-local'

# Run the handler locally
if __name__ == '__main__':
    print("=" * 60)
    print("TESTING LAMBDA FUNCTION LOCALLY")
    print("=" * 60)
    
    result = lambda_handler(test_event, None)
    
    print("\nRESULT:")
    print(json.dumps(result, indent=2))
    
    # Check if any errors
    if result.get('statusCode') == 200:
        body = json.loads(result['body'])
        print(f"\n✅ Success: {body.get('success_count')} URLs processed")
        print(f"❌ Errors: {body.get('error_count')}")
    else:
        print(f"\n❌ Failed: {result}")