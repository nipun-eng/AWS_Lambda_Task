import json
import os
import boto3
from urllib.parse import urlparse
import re

class LambdaAuthHandler:
    """Authentication handler for Lambda (cookies from S3)"""
    
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.s3 = boto3.client('s3')
        self.cookies_prefix = "cookies/"
    
    def load_cookies(self, context, url):
        """Load cookies from S3"""
        domain = self._get_domain_key(url)
        cookie_key = f"{self.cookies_prefix}{domain}_cookies.json"
        
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=cookie_key)
            cookies = json.loads(response['Body'].read().decode('utf-8'))
            context.add_cookies(cookies)
            print(f" Loaded {len(cookies)} cookies from S3: {cookie_key}")
            return True
        except Exception as e:
            print(f"ℹ No saved cookies found for {domain}")
            return False
    
    def save_cookies(self, context, url):
        """Save cookies to S3"""
        domain = self._get_domain_key(url)
        cookie_key = f"{self.cookies_prefix}{domain}_cookies.json"
        cookies = context.cookies()
        
        if cookies:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=cookie_key,
                Body=json.dumps(cookies, indent=2),
                ContentType='application/json'
            )
            print(f" Saved {len(cookies)} cookies to S3: {cookie_key}")
        return cookies
    
    def _get_domain_key(self, url):
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '').split(':')[0]