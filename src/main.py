"""
Main entry point for LinkedIn Scraper
Step 1 + 2: Enhanced CLI with comprehensive error handling and validation
"""

import argparse
import os
import sys
import logging
from datetime import datetime

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.linkedin_scraper import LinkedInScraper
from utils.exceptions import (
    LinkedInScraperError, InvalidProfileURLError, ProfileNotFoundError,
    ProfilePrivateError, NetworkError, RateLimitError, BrowserError,
    DataExtractionError, CaptchaDetectedError, MaxRetriesExceededError
)
from utils.validators import validate_scraping_parameters


def setup_logging(verbose=False):
    """Setup logging configuration"""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/scraper.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce selenium logging noise
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def handle_scraper_error(error):
    """
    Handle different types of scraper errors with appropriate messages
    
    Args:
        error: Exception that occurred
        
    Returns:
        Exit code for the application
    """
    if isinstance(error, InvalidProfileURLError):
        print(f"❌ Invalid Profile URL: {error}")
        print("💡 Please provide a valid LinkedIn profile URL like:")
        print("   https://www.linkedin.com/in/username")
        return 1
    
    elif isinstance(error, ProfileNotFoundError):
        print(f"❌ Profile Not Found: {error}")
        print("💡 The profile may have been deleted or the URL is incorrect")
        return 2
    
    elif isinstance(error, ProfilePrivateError):
        print(f"❌ Private Profile: {error}")
        print("💡 This profile is private and cannot be scraped")
        return 3
    
    elif isinstance(error, CaptchaDetectedError):
        print(f"❌ CAPTCHA Detected: {error}")
        print("💡 LinkedIn has detected automated activity. Try again later or use --no-headless to solve manually")
        return 4
    
    elif isinstance(error, RateLimitError):
        print(f"❌ Rate Limited: {error}")
        print("💡 You're being rate limited by LinkedIn. Wait before trying again")
        return 5
    
    elif isinstance(error, NetworkError):
        print(f"❌ Network Error: {error}")
        print("💡 Check your internet connection and try again")
        return 6
    
    elif isinstance(error, BrowserError):
        print(f"❌ Browser Error: {error}")
        print("💡 Try updating Chrome or running with --no-headless")
        return 7
    
    elif isinstance(error, DataExtractionError):
        print(f"❌ Data Extraction Error: {error}")
        print("💡 Failed to extract data from the profile. The page structure may have changed")
        return 8
    
    elif isinstance(error, MaxRetriesExceededError):
        print(f"❌ Max Retries Exceeded: {error}")
        print("💡 Multiple attempts failed. Try again later")
        return 9
    
    else:
        print(f"❌ Unexpected Error: {error}")
        print("💡 An unexpected error occurred. Check the logs for more details")
        return 10


def main():
    """Main function with enhanced error handling and validation"""
    parser = argparse.ArgumentParser(
        description='LinkedIn Profile Scraper - Step 2: Enhanced Error Handling',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --profile-url "https://linkedin.com/in/username"
  %(prog)s -u "linkedin.com/in/username" --no-headless
  %(prog)s -u "https://linkedin.com/in/username" -o data/profile.json --verbose
        """
    )
    
    parser.add_argument('--profile-url', '-u', required=True, 
                       help='LinkedIn profile URL to scrape')
    parser.add_argument('--output', '-o', 
                       help='Output file path (default: auto-generated)')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Run browser in headless mode (default: True)')
    parser.add_argument('--no-headless', action='store_true',
                       help='Run browser with GUI (overrides --headless)')
    parser.add_argument('--timeout', '-t', type=int, default=30,
                       help='Browser timeout in seconds (default: 30)')
    parser.add_argument('--max-retries', '-r', type=int, default=3,
                       help='Maximum retry attempts (default: 3)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Determine headless mode
    headless = args.headless and not args.no_headless
    
    # Generate output filename if not provided
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        try:
            # Try to extract username for filename
            from utils.validators import URLValidator
            username = URLValidator.extract_username(args.profile_url)
        except:
            username = 'profile'
        args.output = f'data/{username}_{timestamp}.json'
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    print("🚀 LinkedIn Scraper - Step 2: Enhanced Error Handling")
    print(f"Target URL: {args.profile_url}")
    print(f"Output file: {args.output}")
    print(f"Headless mode: {headless}")
    print(f"Timeout: {args.timeout}s")
    print(f"Max retries: {args.max_retries}")
    print(f"Verbose logging: {args.verbose}")
    print("-" * 60)
    
    try:
        # Step 2: Validate parameters before scraping
        logger.info("Validating scraping parameters...")
        validated_params = validate_scraping_parameters(
            profile_url=args.profile_url,
            output_path=args.output,
            headless=headless,
            timeout=args.timeout
        )
        
        logger.info("Parameters validated successfully")
        
        # Initialize and run scraper
        logger.info("Initializing LinkedIn scraper...")
        with LinkedInScraper(
            headless=headless, 
            timeout=args.timeout, 
            max_retries=args.max_retries
        ) as scraper:
            
            logger.info("Starting profile scraping...")
            profile_data = scraper.scrape_profile(validated_params['profile_url'])
            
            if profile_data:
                scraper.save_data(profile_data, args.output)
                
                print(f"✅ Successfully scraped profile data!")
                print(f"📁 Data saved to: {args.output}")
                
                # Print enhanced summary
                print("\n📊 Profile Summary:")
                print(f"Name: {profile_data.get('name', 'N/A')}")
                print(f"Headline: {profile_data.get('headline', 'N/A')}")
                print(f"Location: {profile_data.get('location', 'N/A')}")
                print(f"Experience entries: {len(profile_data.get('experience', []))}")
                print(f"Education entries: {len(profile_data.get('education', []))}")
                print(f"Skills: {len(profile_data.get('skills', []))}")
                
                # Step 2: Show data quality score
                quality_score = profile_data.get('quality_score', 0.0)
                quality_emoji = "🟢" if quality_score > 0.7 else "🟡" if quality_score > 0.4 else "🔴"
                print(f"Data Quality: {quality_emoji} {quality_score:.1%}")
                
                print(f"\n🕒 Scraped at: {profile_data.get('scraped_at', 'N/A')}")
                
            else:
                print("❌ No data was extracted from the profile")
                return 8
    
    except KeyboardInterrupt:
        print("\n🛑 Scraping interrupted by user")
        logger.info("Scraping interrupted by user")
        return 130  # Standard exit code for Ctrl+C
    
    except LinkedInScraperError as e:
        logger.error(f"LinkedIn scraper error: {e}")
        return handle_scraper_error(e)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"❌ Unexpected Error: {str(e)}")
        print("💡 Check the logs/scraper.log file for detailed error information")
        return 10
    
    print("\n🎉 Scraping completed successfully!")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 