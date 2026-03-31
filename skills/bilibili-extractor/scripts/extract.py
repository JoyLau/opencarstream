#!/usr/bin/env python3
"""
Bilibili video extractor - Extract video metadata and save to local API
"""

import sys
import re
import json
import time
import argparse
import urllib.request
import urllib.parse
from datetime import datetime


def resolve_short_link(short_url):
    """Resolve b23.tv short link to full URL"""
    try:
        req = urllib.request.Request(
            short_url,
            method='HEAD',
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.geturl()
    except Exception as e:
        print(f"Error resolving short link: {e}", file=sys.stderr)
        return None


def extract_bvid(url):
    """Extract BV ID from Bilibili URL"""
    # Match BV pattern
    match = re.search(r'BV\w+', url)
    if match:
        return match.group()
    return None


def fetch_video_info(bvid):
    """Fetch video info from Bilibili API"""
    api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    try:
        req = urllib.request.Request(
            api_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com'
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('code') == 0:
                return data.get('data')
            else:
                print(f"API error: {data.get('message')}", file=sys.stderr)
                return None
    except Exception as e:
        print(f"Error fetching video info: {e}", file=sys.stderr)
        return None


def format_views(view_count):
    """Format view count to human readable"""
    if view_count >= 10000:
        return f"{view_count / 10000:.1f}万"
    return str(view_count)


def format_relative_time(timestamp):
    """Convert timestamp to relative time string"""
    now = time.time()
    diff = now - timestamp
    
    if diff < 60:
        return "刚刚"
    elif diff < 3600:
        return f"{int(diff / 60)}分钟前"
    elif diff < 86400:
        return f"{int(diff / 3600)}小时前"
    elif diff < 2592000:
        return f"{int(diff / 86400)}天前"
    elif diff < 31536000:
        return f"{int(diff / 2592000)}个月前"
    else:
        return f"{int(diff / 31536000)}年前"


def transform_data(video_data, query=None):
    """Transform API data to required format"""
    video = {
        "id": video_data['bvid'],
        "title": video_data['title'],
        "duration": str(video_data['duration']),
        "thumb": video_data['pic'],
        "url": f"https://www.bilibili.com/video/{video_data['bvid']}",
        "author": video_data['owner']['name'],
        "views": format_views(video_data['stat']['view']),
        "pub_time": format_relative_time(video_data['pubdate'])
    }
    
    result = {
        "query": query or video_data['title'],
        "videos": [video],
        "saved_at": int(time.time())
    }
    
    return result


def save_to_api(data, api_url="http://192.168.1.27:33333/bili_videos_fill"):
    """POST data to local API"""
    try:
        json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(
            api_url,
            data=json_data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0'
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode('utf-8')
    except Exception as e:
        print(f"Error saving to API: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description='Extract Bilibili video info')
    parser.add_argument('url', help='Bilibili URL (b23.tv or bilibili.com)')
    parser.add_argument('--query', '-q', help='Custom query string (default: video title)')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Print JSON without saving')
    
    args = parser.parse_args()
    
    # Resolve short link if needed
    url = args.url
    if 'b23.tv' in url:
        print(f"Resolving short link: {url}")
        full_url = resolve_short_link(url)
        if not full_url:
            print("Failed to resolve short link", file=sys.stderr)
            sys.exit(1)
        print(f"Resolved to: {full_url}")
        url = full_url
    
    # Extract BV ID
    bvid = extract_bvid(url)
    if not bvid:
        print("Could not extract BV ID from URL", file=sys.stderr)
        sys.exit(1)
    print(f"BV ID: {bvid}")
    
    # Fetch video info
    print("Fetching video info...")
    video_data = fetch_video_info(bvid)
    if not video_data:
        print("Failed to fetch video info", file=sys.stderr)
        sys.exit(1)
    
    # Transform data
    result = transform_data(video_data, args.query)
    
    # Print result
    print("\nExtracted data:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # Save to API
    if not args.dry_run:
        print("\nSaving to API...")
        response = save_to_api(result)
        if response:
            print(f"API response: {response}")
        else:
            print("Failed to save to API", file=sys.stderr)
            sys.exit(1)
    else:
        print("\nDry run mode - not saving to API")


if __name__ == '__main__':
    main()
