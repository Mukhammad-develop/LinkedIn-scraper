"""
Main entry point for LinkedIn Scraper
Step 1: Basic command-line interface for profile scraping
"""

import argparse
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.linkedin_scraper import LinkedInScraper


def main():
    """Main function to run the LinkedIn scraper"""
    parser = argparse.ArgumentParser(description='LinkedIn Profile Scraper - Step 1')
    parser.add_argument('--profile-url', '-u', required=True, 
                       help='LinkedIn profile URL to scrape')
    parser.add_argument('--output', '-o', 
                       help='Output file path (default: auto-generated)')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Run browser in headless mode (default: True)')
    parser.add_argument('--no-headless', action='store_true',
                       help='Run browser with GUI')
    
    args = parser.parse_args()
    
    # Determine headless mode
    headless = args.headless and not args.no_headless
    
    # Generate output filename if not provided
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        profile_name = args.profile_url.split('/')[-1] or 'profile'
        args.output = f'data/{profile_name}_{timestamp}.json'
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    print("🚀 LinkedIn Scraper - Step 1: Basic Profile Scraping")
    print(f"Target URL: {args.profile_url}")
    print(f"Output file: {args.output}")
    print(f"Headless mode: {headless}")
    print("-" * 50)
    
    try:
        # Initialize and run scraper
        with LinkedInScraper(headless=headless) as scraper:
            profile_data = scraper.scrape_profile(args.profile_url)
            
            if profile_data:
                scraper.save_data(profile_data, args.output)
                print(f"✅ Successfully scraped profile data!")
                print(f"📁 Data saved to: {args.output}")
                
                # Print summary
                print("\n📊 Profile Summary:")
                print(f"Name: {profile_data.get('name', 'N/A')}")
                print(f"Headline: {profile_data.get('headline', 'N/A')}")
                print(f"Location: {profile_data.get('location', 'N/A')}")
                print(f"Experience entries: {len(profile_data.get('experience', []))}")
                print(f"Education entries: {len(profile_data.get('education', []))}")
                print(f"Skills: {len(profile_data.get('skills', []))}")
            else:
                print("❌ Failed to scrape profile data")
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\n🛑 Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 