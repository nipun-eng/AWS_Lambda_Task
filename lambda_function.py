import json
import os
import time
import boto3
import base64
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import re
from datetime import datetime
from auth_handler import LambdaAuthHandler

# Initialize S3 client
s3 = boto3.client('s3')

def analyze_tone_of_voice(data):
    """Analyze tone from headlines and text"""
    headlines = data.get('headlines', [])
    text_content = data.get('page_text', '')
    
    tones = {
        'professional': ['expert', 'professional', 'solution', 'enterprise', 'business'],
        'friendly': ['hello', 'welcome', 'friend', 'community', 'hey'],
        'urgent': ['now', 'limited', 'today', 'hurry', 'last chance'],
        'inspirational': ['dream', 'future', 'possibility', 'achieve', 'goal'],
        'youthful': ['fresh', 'cool', 'vibe', 'trending', 'young'],
        'authoritative': ['official', 'leader', 'expert', 'authority']
    }
    
    detected_tones = []
    all_text = ' '.join([h.get('text', '') for h in headlines]) + ' ' + text_content
    all_text = all_text.lower()
    
    for tone, keywords in tones.items():
        if any(keyword in all_text for keyword in keywords):
            detected_tones.append(tone)
    
    return detected_tones or ['neutral']

def analyze_visual_identity(data):
    """Analyze visual elements from images"""
    images = data.get('images', [])
    
    # Count images by type (based on alt text and filenames)
    logo_count = 0
    product_count = 0
    people_count = 0
    screenshot_count = 0
    
    for img in images[:20]:  # Limit analysis to first 20 images
        alt_text = img.get('alt', '').lower()
        src = img.get('src', '').lower()
        
        if 'logo' in alt_text or 'logo' in src:
            logo_count += 1
        elif any(word in alt_text for word in ['product', 'item', 'merch']):
            product_count += 1
        elif any(word in alt_text for word in ['person', 'people', 'user', 'customer', 'face']):
            people_count += 1
        elif 'screenshot' in src or 'screenshot' in alt_text:
            screenshot_count += 1
    
    return {
        'logo_count': logo_count,
        'product_images': product_count,
        'people_images': people_count,
        'screenshots': screenshot_count,
        'total_images_analyzed': min(len(images), 20),
        'color_scheme': 'unknown',  # Would need image processing for actual colors
        'style': extract_visual_style(data.get('screenshot_folder'))
    }

def extract_visual_style(screenshot_folder):
    """Extract visual style from screenshots (simplified)"""
    # In production, you'd use image recognition here
    # For now, return placeholder
    return ['modern', 'minimalist']  # Placeholder

def analyze_audience_sentiment(data):
    """Analyze audience sentiment from comments/interactions"""
    # For social media platforms, look for engagement metrics
    platform_specific = data.get('platform_specific', {})
    
    # Try to extract follower counts, post counts etc
    followers = extract_follower_count(platform_specific)
    posts = extract_post_count(platform_specific)
    
    # Look for engagement indicators in links
    links = data.get('links', {})
    social_links = len(links.get('social', []))
    
    return {
        'follower_count': followers,
        'total_posts': posts,
        'social_mentions': social_links,
        'engagement_level': estimate_engagement(followers, posts),
        'sentiment_score': 0.75,  # Placeholder - would need ML model
        'common_topics': extract_common_topics(data.get('page_text', ''))
    }

def extract_follower_count(platform_data):
    """Extract follower count from platform-specific data"""
    # Placeholder - would need platform-specific selectors
    return 'N/A'

def extract_post_count(platform_data):
    """Extract post count from platform-specific data"""
    return 'N/A'

def estimate_engagement(followers, posts):
    """Estimate engagement level"""
    if followers == 'N/A' or posts == 'N/A':
        return 'unknown'
    return 'medium'  # Placeholder

def extract_common_topics(text):
    """Extract common topics from text"""
    # Simplified - would use NLP in production
    topics = ['fashion', 'lifestyle', 'sports']  # Placeholder
    return topics

def analyze_core_values(data):
    """Extract core brand values from metadata and content"""
    metadata = data.get('metadata', {})
    description = metadata.get('description', '').lower()
    keywords = metadata.get('keywords', '').lower()
    headlines = data.get('headlines', [])
    
    # Common brand values with keywords
    values_keywords = {
        'innovation': ['innovative', 'cutting-edge', 'future', 'technology', 'tech'],
        'quality': ['quality', 'premium', 'excellence', 'best', 'superior'],
        'sustainability': ['sustainable', 'eco-friendly', 'green', 'environment', 'planet'],
        'customer_focus': ['customer', 'client', 'service', 'support', 'help'],
        'integrity': ['trust', 'integrity', 'honest', 'transparent', 'ethical'],
        'community': ['community', 'together', 'belonging', 'family', 'team'],
        'diversity': ['diverse', 'inclusion', 'equality', 'everyone'],
        'performance': ['performance', 'powerful', 'fast', 'efficient', 'results']
    }
    
    # Collect all text to analyze
    all_text = description + ' ' + keywords + ' '
    for h in headlines[:5]:
        all_text += h.get('text', '').lower() + ' '
    
    detected_values = []
    for value, keywords_list in values_keywords.items():
        if any(keyword in all_text for keyword in keywords_list):
            detected_values.append(value)
    
    return detected_values

def scrape_social_media(page, url, platform):
    """
    Platform-specific scraping logic
    """
    platform_data = {
        'platform': platform,
        'profile_info': {},
        'posts': []
    }
    
    try:
        if 'instagram.com' in platform:
            # Instagram specific scraping
            platform_data['profile_info']['bio'] = extract_text_safe(page, 'span[class*="bio"]')
            platform_data['profile_info']['followers'] = extract_text_safe(page, 'span[class*="followers"]')
            platform_data['profile_info']['following'] = extract_text_safe(page, 'span[class*="following"]')
            platform_data['profile_info']['posts_count'] = extract_text_safe(page, 'span[class*="posts"]')
            
            # Get recent posts
            posts = page.query_selector_all('article')[0:3]  # First 3 posts
            for i, post in enumerate(posts):
                platform_data['posts'].append({
                    'index': i,
                    'caption': extract_text_safe(post, 'span[class*="caption"]'),
                    'likes': extract_text_safe(post, 'section span'),
                    'comments': extract_text_safe(post, 'section a span')
                })
                
        elif 'tiktok.com' in platform:
            # TikTok specific
            platform_data['profile_info']['bio'] = extract_text_safe(page, 'h2')
            platform_data['profile_info']['followers'] = extract_text_safe(page, 'strong[data-e2e="followers-count"]')
            platform_data['profile_info']['likes'] = extract_text_safe(page, 'strong[data-e2e="likes-count"]')
            
        elif 'twitter.com' in platform or 'x.com' in platform:
            # X/Twitter specific
            platform_data['profile_info']['bio'] = extract_text_safe(page, 'div[data-testid="UserDescription"]')
            platform_data['profile_info']['followers'] = extract_text_safe(page, 'a[href*="/followers"] span')
            platform_data['profile_info']['following'] = extract_text_safe(page, 'a[href*="/following"] span')
            
            # Get recent tweets
            tweets = page.query_selector_all('article')[0:3]
            for i, tweet in enumerate(tweets):
                platform_data['posts'].append({
                    'index': i,
                    'text': extract_text_safe(tweet, 'div[data-testid="tweetText"]'),
                    'metrics': {
                        'replies': extract_text_safe(tweet, 'button[data-testid="reply"] span'),
                        'retweets': extract_text_safe(tweet, 'button[data-testid="retweet"] span'),
                        'likes': extract_text_safe(tweet, 'button[data-testid="like"] span')
                    }
                })
    
    except Exception as e:
        print(f"Platform scraping error: {e}")
    
    return platform_data

def extract_text_safe(element, selector):
    """Safely extract text from an element"""
    try:
        el = element.query_selector(selector)
        return el.inner_text() if el else None
    except:
        return None

def scrape_general_data(page, url):
    """Scrape general page data"""
    data = {
        'url': url,
        'title': page.title(),
        'headlines': [],
        'images': [],
        'metadata': {},
        'links': {'internal': [], 'external': [], 'social': []},
        'page_text': ''
    }
    
    # Get page text (limited size)
    body = page.query_selector('body')
    if body:
        data['page_text'] = body.inner_text()[:10000]  # Limit to 10KB
    
    # Get headlines
    for heading in ['h1', 'h2', 'h3']:
        elements = page.query_selector_all(heading)
        for elem in elements[:10]:  # Limit to 10 per heading type
            text = elem.inner_text().strip()
            if text and len(text) < 200:  # Avoid huge blocks
                data['headlines'].append({
                    'type': heading,
                    'text': text[:100]  # Limit length
                })
    
    # Get images
    images = page.query_selector_all('img')
    for i, img in enumerate(images[:20]):  # Limit to 20 images
        src = img.get_attribute('src')
        if src and not src.startswith('data:'):  # Skip data URIs
            data['images'].append({
                'src': src[:200],  # Limit URL length
                'alt': (img.get_attribute('alt') or '')[:100],
                'width': img.get_attribute('width'),
                'height': img.get_attribute('height')
            })
    
    # Get metadata
    data['metadata']['description'] = get_meta_content(page, 'description')
    data['metadata']['keywords'] = get_meta_content(page, 'keywords')
    data['metadata']['author'] = get_meta_content(page, 'author')
    
    # Get social links
    all_links = page.query_selector_all('a')
    social_patterns = ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'tiktok']
    for link in all_links[:50]:  # Limit to 50 links
        href = link.get_attribute('href')
        if href:
            if any(pattern in href.lower() for pattern in social_patterns):
                data['links']['social'].append({'url': href[:200]})
    
    return data

def get_meta_content(page, name):
    """Get meta tag content"""
    meta = page.query_selector(f'meta[name="{name}"]')
    return meta.get_attribute('content') if meta else None

def save_results_to_s3(data, insights, url, bucket_name):
    """Save scraped data and insights to S3"""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    domain = urlparse(url).netloc.replace('www.', '')
    safe_domain = re.sub(r'[^\w\.-]', '_', domain)
    
    # Save raw data
    raw_key = f"raw_data/{safe_domain}/{timestamp}/scraped_data.json"
    s3.put_object(
        Bucket=bucket_name,
        Key=raw_key,
        Body=json.dumps(data, indent=2, default=str),
        ContentType='application/json'
    )
    
    # Save insights
    insights_key = f"insights/{safe_domain}/{timestamp}/brand_psychology.json"
    s3.put_object(
        Bucket=bucket_name,
        Key=insights_key,
        Body=json.dumps(insights, indent=2, default=str),
        ContentType='application/json'
    )
    
    return {
        'raw_data': raw_key,
        'insights': insights_key,
        'timestamp': timestamp
    }

def lambda_handler(event, context):
    """
    Main Lambda handler
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Get URLs from event
        urls = event.get('urls', [])
        bucket_name = os.environ.get('S3_BUCKET_NAME', 'brand-insights-bucket')
        
        if not urls:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No URLs provided'})
            }
        
        all_results = []
        
        with sync_playwright() as p:
            # Launch browser (optimized for Lambda)
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-gpu',
                    '--single-process',
                    '--no-zygote'
                ]
            )
            
            context_browser = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            auth_handler = LambdaAuthHandler(bucket_name)
            page = context_browser.new_page()
            page.set_default_timeout(30000)  # 30 second timeout
            
            for url in urls:
                print(f"Processing: {url}")
                url_result = {'url': url, 'status': 'processing'}
                
                try:
                    # Try to load saved cookies
                    auth_handler.load_cookies(context_browser, url)
                    
                    # Navigate to page
                    print(f"Navigating to {url}")
                    page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    time.sleep(3)
                    
                    # Determine platform
                    platform = urlparse(url).netloc
                    
                    # Scrape platform-specific data
                    platform_data = scrape_social_media(page, url, platform)
                    
                    # Scrape general data
                    scraped_data = scrape_general_data(page, url)
                    scraped_data['platform_specific'] = platform_data
                    
                    # Extract brand psychology insights
                    insights = {
                        'tone_of_voice': analyze_tone_of_voice(scraped_data),
                        'visual_identity': analyze_visual_identity(scraped_data),
                        'audience_sentiment': analyze_audience_sentiment(scraped_data),
                        'core_values': analyze_core_values(scraped_data),
                        'timestamp': datetime.utcnow().isoformat(),
                        'platform': platform
                    }
                    
                    # Save to S3
                    s3_location = save_results_to_s3(scraped_data, insights, url, bucket_name)
                    
                    url_result.update({
                        'status': 'success',
                        'platform': platform,
                        'insights': insights,
                        's3_location': s3_location
                    })
                    
                    print(f"Successfully processed {url}")
                    
                except Exception as e:
                    print(f"Error processing {url}: {str(e)}")
                    url_result.update({
                        'status': 'error',
                        'error': str(e)
                    })
                
                all_results.append(url_result)
                time.sleep(2)  # Delay between URLs
            
            browser.close()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed URLs',
                'results': all_results,
                'total_processed': len(all_results),
                'success_count': sum(1 for r in all_results if r['status'] == 'success'),
                'error_count': sum(1 for r in all_results if r['status'] == 'error')
            }, indent=2, default=str)
        }
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

# LambdaAuthHandler class will be in auth_handler.py