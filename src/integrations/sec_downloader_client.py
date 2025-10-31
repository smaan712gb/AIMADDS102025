"""
Production-safe SEC filing downloader using sec-edgar-downloader
This complements (doesn't replace) the existing sec_client.py
"""
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger
from sec_edgar_downloader import Downloader


class SECDownloaderClient:
    """
    Wrapper for sec-edgar-downloader library
    Provides reliable SEC filing downloads
    """
    
    def __init__(self, company_name: str = "AIMADDS", email: str = "analysis@aimadds.com"):
        """
        Initialize SEC downloader
        
        Args:
            company_name: Your company name (required by SEC)
            email: Your email (required by SEC)
        """
        self.company_name = company_name
        self.email = email
        self.download_folder = Path("data/sec_filings")
        self.download_folder.mkdir(parents=True, exist_ok=True)
        
        # Initialize downloader with proper user agent
        self.downloader = Downloader(
            self.company_name,
            self.email,
            self.download_folder
        )
        
        logger.info(f"SEC Downloader initialized: {self.company_name} <{self.email}>")
    
    def download_10k(
        self,
        ticker: str,
        num_filings: int = 1,
        after_date: Optional[str] = None,
        before_date: Optional[str] = None
    ) -> List[Path]:
        """
        Download 10-K filings for a company
        
        Args:
            ticker: Stock ticker
            num_filings: Number of filings to download
            after_date: Download filings after this date (YYYY-MM-DD)
            before_date: Download filings before this date (YYYY-MM-DD)
            
        Returns:
            List of paths to downloaded filing files
        """
        try:
            logger.info(f"Downloading {num_filings} 10-K filings for {ticker}")
            
            # Download filings
            num_downloaded = self.downloader.get(
                "10-K",
                ticker,
                amount=num_filings,
                after=after_date,
                before=before_date
            )
            
            logger.info(f"✓ Downloaded {num_downloaded} 10-K filings for {ticker}")
            
            # Find downloaded files
            ticker_folder = self.download_folder / "sec-edgar-filings" / ticker / "10-K"
            
            if not ticker_folder.exists():
                logger.error(f"Download folder not found: {ticker_folder}")
                return []
            
            # Collect all .txt files (SEC filings)
            filing_files = []
            for filing_dir in ticker_folder.iterdir():
                if filing_dir.is_dir():
                    txt_files = list(filing_dir.glob("*.txt"))
                    filing_files.extend(txt_files)
            
            logger.info(f"✓ Found {len(filing_files)} filing files")
            return filing_files
            
        except Exception as e:
            logger.error(f"Error downloading 10-K for {ticker}: {e}")
            return []
    
    def read_filing_text(self, filing_path: Path) -> str:
        """
        Read filing text from downloaded file
        
        Args:
            filing_path: Path to filing file
            
        Returns:
            Full text content of filing
        """
        try:
            with open(filing_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            logger.info(f"✓ Read filing: {filing_path.name} ({len(content)} chars)")
            return content
            
        except Exception as e:
            logger.error(f"Error reading filing {filing_path}: {e}")
            return ""
