"""
Test script for the recursive crawler.
"""

import os
import sys
import time
from crawl import recursive_crawl

def main():
    """
    Run the recursive crawler and demonstrate its functionality.
    """
    # Starting URL
    start_url = "https://www.metropoleballard.com/home"
    
    # Create data directory if it doesn't exist
    os.makedirs('data/html', exist_ok=True)
    
    print(f"Starting recursive crawl from {start_url}")
    print("This will collect all internal links and store the HTML content.")
    print("Press Ctrl+C to stop the crawl at any time.")
    
    try:
        # Run the crawler with a limit of 50 pages and save to files
        start_time = time.time()
        content_dict = recursive_crawl(start_url, max_pages=50, save_to_files=True)
        end_time = time.time()
        
        # Print results
        print("\nCrawl completed!")
        print(f"Time taken: {end_time - start_time:.2f} seconds")
        print(f"Pages crawled: {len(content_dict)}")
        
        # Print the URLs that were crawled
        print("\nCrawled URLs:")
        for i, url in enumerate(content_dict.keys(), 1):
            print(f"{i}. {url}")
        
        # Check if files were saved
        html_files = os.listdir('data/html')
        print(f"\nHTML files saved: {len(html_files)}")
        
        # Print some sample file names
        if html_files:
            print("\nSample saved files:")
            for file in html_files[:5]:
                print(f"- data/html/{file}")
            
            if len(html_files) > 5:
                print(f"... and {len(html_files) - 5} more")
        
    except KeyboardInterrupt:
        print("\nCrawl interrupted by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
