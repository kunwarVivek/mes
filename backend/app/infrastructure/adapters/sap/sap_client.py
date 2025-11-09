"""
SAP Client - Connection Management
Handles OData/RFC connections to SAP systems with retry logic
"""
import httpx
from typing import Any, Dict, List, Optional
from .config import SAPConfig
from .exceptions import SAPConnectionError, SAPAuthenticationError, SAPTimeoutError
import logging

logger = logging.getLogger(__name__)


class SAPClient:
    """SAP OData/RFC client for managing connections and executing queries"""

    def __init__(self, config: SAPConfig):
        """
        Initialize SAP client with configuration

        Args:
            config: SAP connection configuration
        """
        self.config = config
        self.is_connected = False
        self._http_client: Optional[httpx.AsyncClient] = None
        self._base_url = f"https://{config.host}"
        if config.port:
            self._base_url = f"https://{config.host}:{config.port}"

    async def connect(self) -> None:
        """
        Establish connection to SAP OData service

        Raises:
            SAPConnectionError: If connection fails
            SAPAuthenticationError: If authentication fails
        """
        try:
            self._http_client = httpx.AsyncClient(
                auth=(self.config.user, self.config.password),
                timeout=self.config.timeout,
                verify=self.config.ssl_verify
            )

            # Test connection with a simple query
            response = await self._http_client.get(f"{self._base_url}/sap/opu/odata/sap/API_MATERIAL/")

            if response.status_code == 401:
                raise SAPAuthenticationError("Authentication failed: Invalid credentials")

            if response.status_code >= 400:
                raise SAPConnectionError(f"Connection failed with status {response.status_code}")

            self.is_connected = True
            logger.info(f"Connected to SAP system at {self.config.host}")

        except httpx.TimeoutException as e:
            raise SAPConnectionError(f"Connection timeout: {str(e)}")
        except httpx.HTTPError as e:
            raise SAPConnectionError(f"HTTP error during connection: {str(e)}")

    async def disconnect(self) -> None:
        """Disconnect from SAP service and cleanup resources"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        self.is_connected = False
        logger.info("Disconnected from SAP system")

    async def execute_query(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute OData query with retry logic

        Args:
            endpoint: OData endpoint path
            params: Query parameters

        Returns:
            List of result records

        Raises:
            SAPConnectionError: If query fails after retries
        """
        if not self._http_client:
            raise SAPConnectionError("Client not connected. Call connect() first.")

        retry_count = 0
        last_exception = None

        while retry_count <= self.config.max_retries:
            try:
                url = f"{self._base_url}{endpoint}"
                response = await self._http_client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    # Parse OData response structure
                    if "d" in data and "results" in data["d"]:
                        return data["d"]["results"]
                    elif "d" in data:
                        return [data["d"]] if isinstance(data["d"], dict) else data["d"]
                    return []

                elif response.status_code >= 400:
                    raise SAPConnectionError(f"Query failed with status {response.status_code}")

            except httpx.TimeoutException as e:
                last_exception = e
                retry_count += 1
                logger.warning(f"Query timeout, retry {retry_count}/{self.config.max_retries}")
                if retry_count > self.config.max_retries:
                    raise SAPConnectionError(f"Max retries exceeded: {str(e)}")
                continue

            except httpx.HTTPError as e:
                raise SAPConnectionError(f"HTTP error during query: {str(e)}")

        raise SAPConnectionError(f"Max retries exceeded: {str(last_exception)}")

    async def execute_post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute OData POST request

        Args:
            endpoint: OData endpoint path
            data: Payload to post

        Returns:
            Response data

        Raises:
            SAPConnectionError: If POST fails
        """
        if not self._http_client:
            raise SAPConnectionError("Client not connected. Call connect() first.")

        try:
            url = f"{self._base_url}{endpoint}"
            response = await self._http_client.post(url, json=data)

            if response.status_code in (200, 201):
                response_data = response.json()
                # Parse OData response
                if "d" in response_data:
                    return response_data["d"]
                return response_data

            raise SAPConnectionError(f"POST failed with status {response.status_code}")

        except httpx.TimeoutException as e:
            raise SAPTimeoutError(f"POST timeout: {str(e)}")
        except httpx.HTTPError as e:
            raise SAPConnectionError(f"HTTP error during POST: {str(e)}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
