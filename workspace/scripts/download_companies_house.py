#!/usr/bin/env python3
"""
Companies House Data Downloader

Downloads the Free Company Data Product from Companies House.
https://download.companieshouse.gov.uk/en_output.html

The data is updated monthly (within 5 working days of month end).
File naming convention: BasicCompanyDataAsOneFile-YYYY-MM-01.zip

Usage:
    python3 workspace/scripts/download_companies_house.py              # Download latest
    python3 workspace/scripts/download_companies_house.py --date 2025-12-01  # Specific date
    python3 workspace/scripts/download_companies_house.py --list       # List available files
    python3 workspace/scripts/download_companies_house.py --keep-zip   # Don't delete ZIP after extract
"""

import argparse
import sys
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = "https://download.companieshouse.gov.uk"
FILE_PREFIX = "BasicCompanyDataAsOneFile"

# Output directory (relative to project root)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "workspace" / "raw_data"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_latest_data_date():
    """
    Calculate the expected date for the latest Companies House data.
    
    Data is published within 5 working days of month end, dated the 1st of that month.
    So in December 2025, we'd expect the file dated 2025-12-01.
    
    If we're in the first week of a month, the previous month's file might be latest.
    """
    today = datetime.now()
    
    # If we're past the 5th, this month's file should be available
    # Otherwise, use previous month
    if today.day > 7:
        return datetime(today.year, today.month, 1)
    else:
        # Go to previous month
        first_of_this_month = datetime(today.year, today.month, 1)
        last_month = first_of_this_month - timedelta(days=1)
        return datetime(last_month.year, last_month.month, 1)


def format_date(dt):
    """Format datetime as YYYY-MM-DD for URL."""
    return dt.strftime("%Y-%m-%d")


def build_download_url(date_str):
    """Build the download URL for a given date."""
    return f"{BASE_URL}/{FILE_PREFIX}-{date_str}.zip"


def check_url_exists(url):
    """Check if a URL exists (HEAD request)."""
    try:
        req = Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0 (Companies House Data Downloader)')
        with urlopen(req, timeout=10) as response:
            return response.status == 200
    except (HTTPError, URLError):
        return False


def get_file_size(url):
    """Get file size from URL headers."""
    try:
        req = Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0 (Companies House Data Downloader)')
        with urlopen(req, timeout=10) as response:
            content_length = response.headers.get('Content-Length')
            if content_length:
                return int(content_length)
    except (HTTPError, URLError):
        pass
    return None


def format_size(size_bytes):
    """Format bytes as human-readable size."""
    if size_bytes is None:
        return "unknown size"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def download_file(url, output_path, chunk_size=8192):
    """Download a file with progress reporting."""
    req = Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Companies House Data Downloader)')
    
    with urlopen(req) as response:
        total_size = response.headers.get('Content-Length')
        total_size = int(total_size) if total_size else None
        
        downloaded = 0
        with open(output_path, 'wb') as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                
                # Progress reporting
                if total_size:
                    pct = (downloaded / total_size) * 100
                    print(f"\r  Downloading: {format_size(downloaded)} / {format_size(total_size)} ({pct:.1f}%)", end='', flush=True)
                else:
                    print(f"\r  Downloading: {format_size(downloaded)}", end='', flush=True)
        
        print()  # Newline after progress
    
    return downloaded


def extract_zip(zip_path, output_dir):
    """Extract ZIP file and return list of extracted files."""
    extracted = []
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.namelist():
            print(f"  Extracting: {member}")
            zf.extract(member, output_dir)
            extracted.append(output_dir / member)
    return extracted


def find_available_files(months_back=6):
    """Check which recent months have available data files."""
    available = []
    today = datetime.now()
    
    for i in range(months_back):
        # Calculate date for each month going back
        check_date = datetime(today.year, today.month, 1)
        for _ in range(i):
            check_date = (check_date - timedelta(days=1)).replace(day=1)
        
        date_str = format_date(check_date)
        url = build_download_url(date_str)
        
        if check_url_exists(url):
            size = get_file_size(url)
            available.append((date_str, url, size))
    
    return available


# =============================================================================
# MAIN COMMANDS
# =============================================================================

def cmd_list():
    """List available data files."""
    print("\nChecking available Companies House data files...")
    print("-" * 70)
    
    available = find_available_files(months_back=12)
    
    if not available:
        print("No files found. The service may be temporarily unavailable.")
        return 1
    
    print(f"\n{'Date':<15} {'Size':<15} URL")
    print("-" * 70)
    for date_str, url, size in available:
        print(f"{date_str:<15} {format_size(size):<15} {url}")
    
    print("-" * 70)
    print(f"\nFound {len(available)} available file(s)")
    print("\nTo download: python3 download_companies_house.py --date YYYY-MM-01")
    return 0


def cmd_download(date_str, keep_zip=False):
    """Download and extract Companies House data."""
    url = build_download_url(date_str)
    zip_filename = f"{FILE_PREFIX}-{date_str}.zip"
    zip_path = OUTPUT_DIR / zip_filename
    
    print(f"\n{'='*60}")
    print("COMPANIES HOUSE DATA DOWNLOADER")
    print(f"{'='*60}")
    print(f"\nSource: {url}")
    print(f"Output: {OUTPUT_DIR}")
    
    # Check if URL exists
    print("\nChecking file availability...")
    if not check_url_exists(url):
        print(f"\n❌ File not found: {url}")
        print("\nThe file may not exist yet. Data is published within 5 working days")
        print("of month end. Try --list to see available files.")
        return 1
    
    # Get file size
    size = get_file_size(url)
    print(f"✓ File available: {format_size(size)}")
    
    # Check if already downloaded
    csv_filename = f"{FILE_PREFIX}-{date_str}.csv"
    csv_path = OUTPUT_DIR / csv_filename
    if csv_path.exists():
        print(f"\n⚠️  CSV already exists: {csv_path.name}")
        response = input("   Overwrite? [y/N]: ").strip().lower()
        if response != 'y':
            print("   Aborted.")
            return 0
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Download
    print(f"\nDownloading {zip_filename}...")
    try:
        download_file(url, zip_path)
        print(f"✓ Downloaded: {format_size(zip_path.stat().st_size)}")
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        return 1
    
    # Extract
    print(f"\nExtracting...")
    try:
        extracted = extract_zip(zip_path, OUTPUT_DIR)
        for f in extracted:
            print(f"✓ Extracted: {f.name} ({format_size(f.stat().st_size)})")
    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        return 1
    
    # Cleanup ZIP
    if not keep_zip:
        print(f"\nCleaning up ZIP file...")
        zip_path.unlink()
        print(f"✓ Removed: {zip_filename}")
    
    print(f"\n{'='*60}")
    print("✅ DOWNLOAD COMPLETE")
    print(f"{'='*60}")
    print(f"\nData file: {OUTPUT_DIR / csv_filename}")
    print(f"\nNext: Run the data mapper to load into Neo4j:")
    print(f"  python3 workspace/generated/data_mapper.py")
    
    return 0


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Download Companies House Free Company Data Product",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Download latest available file
  %(prog)s --date 2025-12-01  # Download specific month's file
  %(prog)s --list             # List available files
  %(prog)s --keep-zip         # Keep ZIP file after extraction

Data source: https://download.companieshouse.gov.uk/en_output.html
        """
    )
    
    parser.add_argument(
        "--date", "-d",
        type=str,
        help="Date of data file (YYYY-MM-01 format). Defaults to latest."
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available data files"
    )
    
    parser.add_argument(
        "--keep-zip",
        action="store_true",
        help="Keep ZIP file after extraction"
    )
    
    args = parser.parse_args()
    
    # Handle --list
    if args.list:
        return cmd_list()
    
    # Determine date to download
    if args.date:
        # Validate date format
        try:
            parsed = datetime.strptime(args.date, "%Y-%m-%d")
            if parsed.day != 1:
                print(f"⚠️  Note: Companies House files are always dated the 1st.")
                args.date = format_date(datetime(parsed.year, parsed.month, 1))
        except ValueError:
            print(f"❌ Invalid date format: {args.date}")
            print("   Expected: YYYY-MM-01 (e.g., 2025-12-01)")
            return 1
        date_str = args.date
    else:
        # Calculate latest expected date
        latest = get_latest_data_date()
        date_str = format_date(latest)
        print(f"Auto-detected latest file date: {date_str}")
    
    return cmd_download(date_str, keep_zip=args.keep_zip)


if __name__ == "__main__":
    sys.exit(main())

