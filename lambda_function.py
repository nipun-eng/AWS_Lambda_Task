import os
import time
import json
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
from datetime import datetime

# Set environment variables for Lambda-optimized Chromium
os.environ['PLAYWRIGHT_CHROMIUM_DOWNLOAD_HOST'] = 'https://files.chromiumforlambda.org/amazon-linux-2/x86_64'
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/tmp'

# ... (keep all your analysis functions: analyze_tone_of_voice, analyze_visual_identity, etc.)

def lambda_handler(event, context):
    """Main Lambda handler with optimized Chromium"""
    
    print(f"Received event: {json.dumps(event)}")
    
    try:
        urls = event.get('urls', [])
        
        if not urls:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No URLs provided'})
            }
        
        all_results = []
        
        with sync_playwright() as p:
            # Launch browser with Lambda-optimized settings
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--single-process',
                    '--disable-gpu',
                    '--no-zygote',
                    '--disable-setuid-sandbox'
                ]
            )
            
            page = browser.new_page()
            page.set_default_timeout(30000)
            
            for url in urls:
                print(f"Processing: {url}")
                url_result = {'url': url}
                
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    time.sleep(2)
                    
                    # Your existing scraping logic
                    platform = urlparse(url).netloc
                    scraped_data = scrape_general_data(page, url)
                    
                    # Extract insights
                    insights = {
                        'url': url,
                        'platform': platform,
                        'timestamp': datetime.utcnow().isoformat(),
                        'brand_psychology': {
                            'tone_of_voice': analyze_tone_of_voice(scraped_data),
                            'visual_identity': analyze_visual_identity(scraped_data),
                            'audience_sentiment': analyze_audience_sentiment(scraped_data),
                            'core_values': analyze_core_values(scraped_data)
                        }
                    }
                    
                    url_result.update({
                        'status': 'success',
                        'data': insights
                    })
                    
                except Exception as e:
                    print(f"Error: {str(e)}")
                    url_result.update({'status': 'error', 'error': str(e)})
                
                all_results.append(url_result)
                time.sleep(1)
            
            browser.close()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed URLs',
                'results': all_results,
                'summary': {
                    'total': len(all_results),
                    'successful': sum(1 for r in all_results if r['status'] == 'success'),
                    'failed': sum(1 for r in all_results if r['status'] == 'error')
                }
            }, indent=2)
        }
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

# Include all your analysis functions here
def scrape_general_data(page, url):
    """Your existing scrape_general_data function"""
    # ... paste your existing function here

def analyze_tone_of_voice(data):
    """Your existing tone analysis"""
    # ... paste your existing function here

# ... and all other analysis functions