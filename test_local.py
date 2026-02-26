import json
from lambda_function import lambda_handler

# Test with actual URLs
test_event = {
    'urls': [
        'https://www.instagram.com/nike',
        'https://twitter.com/nike'
    ]
}

if __name__ == '__main__':
    
    print("TESTING BRAND INSIGHTS LAMBDA")
    
    
    result = lambda_handler(test_event, None)
    
    # Parse and pretty print the result
    if result.get('statusCode') == 200:
        body = json.loads(result['body'])
        print(f"\n Success! Processed {body['summary']['successful']} URLs")
        
        # Show insights for each URL
        for item in body['results']:
            if item['status'] == 'success':
                print(f"\n {item['url']}")
                print(f"   Tone: {item['data']['brand_psychology']['tone_of_voice']}")
                print(f"   Values: {item['data']['brand_psychology']['core_values']}")
                print(f"   Visual: {item['data']['brand_psychology']['visual_identity']}")
    else:
        print(f"\n Failed: {result}")