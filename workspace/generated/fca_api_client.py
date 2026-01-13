"""
FCA Handbook API Client

Handles all HTTP communication with the FCA Handbook REST API.
"""

import sys
import os
from typing import Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.logger import log
from workspace.generated.fca_models import LoaderConfig
from workspace.generated.fca_exceptions import TransientAPIError, PermanentAPIError


class FCAAPIClient:
    """
    Client for interacting with the FCA Handbook REST API

    Features:
    - Automatic retry logic for transient errors
    - Connection pooling
    - Proper error handling and classification
    """

    def __init__(self, config: LoaderConfig):
        """
        Initialize API client

        Args:
            config: Loader configuration object
        """
        self.config = config
        self.session = self._create_retry_session()

    def _create_retry_session(self) -> requests.Session:
        """
        Create a requests session with automatic retry logic

        Returns:
            Configured requests.Session with retry adapter
        """
        session = requests.Session()

        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=self.config.retry_status_codes,
            allowed_methods=["GET", "POST"],
            raise_on_status=False
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _handle_response(self, response: requests.Response, context: str) -> Dict:
        """
        Handle API response and raise appropriate exceptions

        Args:
            response: HTTP response object
            context: Context description for error messages

        Returns:
            Parsed JSON response

        Raises:
            TransientAPIError: For retryable errors
            PermanentAPIError: For permanent errors
        """
        # Check HTTP status
        if response.status_code in self.config.retry_status_codes:
            retry_after = response.headers.get('Retry-After')
            raise TransientAPIError(
                f"Transient error for {context}: HTTP {response.status_code}",
                status_code=response.status_code,
                retry_after=int(retry_after) if retry_after else None
            )
        elif response.status_code >= 400:
            raise PermanentAPIError(
                f"Permanent error for {context}: HTTP {response.status_code}",
                status_code=response.status_code
            )

        # Parse JSON
        try:
            data = response.json()
        except ValueError as e:
            raise PermanentAPIError(f"Invalid JSON response for {context}: {e}")

        # Check API success flag
        if not data.get('Success'):
            error_msg = data.get('Error', 'Unknown error')
            # Determine if error is transient or permanent based on message
            if 'timeout' in error_msg.lower() or 'temporarily unavailable' in error_msg.lower():
                raise TransientAPIError(f"API returned error for {context}: {error_msg}")
            else:
                raise PermanentAPIError(f"API returned error for {context}: {error_msg}")

        return data

    def get_all_handbooks(self) -> Dict[str, str]:
        """
        Fetch all available handbooks from the FCA API

        Returns:
            Dictionary mapping handbook codes (lowercase) to full names

        Raises:
            TransientAPIError: For retryable errors
            PermanentAPIError: For permanent errors
        """
        url = f"{self.config.api_base_url}{self.config.all_handbooks_endpoint}"
        params = {'Date': '31-07-2023'}  # Use a stable date for consistency

        try:
            response = self.session.get(url, params=params, timeout=self.config.request_timeout)
            data = self._handle_response(response, "handbooks list")

            result = data.get('Result', {})
            headers = result.get('headers', [])

            handbooks = {}
            for header in headers:
                for part in header.get('parts', []):
                    code = part.get('contains')
                    name = part.get('name')
                    if code:
                        handbooks[code.lower()] = name

            log.info(f"Discovered {len(handbooks)} available handbooks from API")
            return handbooks

        except (TransientAPIError, PermanentAPIError):
            raise
        except requests.RequestException as e:
            raise TransientAPIError(f"Network error fetching handbooks: {e}")
        except Exception as e:
            log.error(f"Unexpected error fetching handbooks: {e}")
            raise PermanentAPIError(f"Unexpected error: {e}")

    def fetch_timeline_entries(self, chapter_id: str) -> List[str]:
        """
        Fetch all historical timeline dates for a chapter

        Args:
            chapter_id: Chapter identifier (e.g., "prin1")

        Returns:
            List of dates in DD-MM-YYYY format, ordered newest to oldest

        Raises:
            TransientAPIError: For retryable errors
            PermanentAPIError: For permanent errors
        """
        url = f"{self.config.api_base_url}{self.config.timeline_endpoint}/{chapter_id}"
        log.debug(f"Fetching timeline for {chapter_id}")

        try:
            response = self.session.get(url, timeout=self.config.request_timeout)
            data = self._handle_response(response, f"{chapter_id} timeline")

            timeline_entries = data.get('Result', {}).get('timelineEntries', [])
            log.info(f"Found {len(timeline_entries)} historical versions for {chapter_id}")
            return timeline_entries

        except (TransientAPIError, PermanentAPIError):
            raise
        except requests.RequestException as e:
            raise TransientAPIError(f"Network error fetching timeline for {chapter_id}: {e}")
        except Exception as e:
            log.error(f"Unexpected error fetching timeline for {chapter_id}: {e}")
            raise PermanentAPIError(f"Unexpected error: {e}")

    def fetch_chapter_data(self, chapter_id: str, date: Optional[str] = None) -> Optional[Dict]:
        """
        Fetch chapter data from FCA API

        Args:
            chapter_id: Chapter identifier (e.g., "prin1", "prin2")
            date: Optional date in DD-MM-YYYY format for historical data

        Returns:
            Dictionary with chapter data

        Raises:
            TransientAPIError: For retryable errors
            PermanentAPIError: For permanent errors
        """
        fetch_date = date or self.config.load_date

        if fetch_date:
            url = f"{self.config.api_base_url}{self.config.chapter_endpoint}/{chapter_id}?Date={fetch_date}&IsDeleted=false"
            log.debug(f"Fetching {chapter_id} at date {fetch_date}")
        else:
            url = f"{self.config.api_base_url}{self.config.chapter_endpoint}/{chapter_id}?IsDeleted=false"
            log.debug(f"Fetching current {chapter_id}")

        try:
            response = self.session.get(url, timeout=self.config.request_timeout)
            data = self._handle_response(response, chapter_id)
            return data.get('Result')

        except (TransientAPIError, PermanentAPIError):
            raise
        except requests.RequestException as e:
            raise TransientAPIError(f"Network error fetching {chapter_id}: {e}")
        except Exception as e:
            log.error(f"Unexpected error fetching {chapter_id}: {e}")
            raise PermanentAPIError(f"Unexpected error: {e}")

    def close(self):
        """Close the HTTP session"""
        if self.session:
            self.session.close()
