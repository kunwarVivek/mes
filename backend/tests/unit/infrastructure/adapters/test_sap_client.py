"""
Unit tests for SAP Client - Connection Management
RED Phase: Write failing tests first
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime


class TestSAPClientConnection:
    """Test SAP client connection management"""

    def test_sap_client_initialization_with_valid_config(self):
        """Should initialize SAP client with valid configuration"""
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass",
            system_number="00"
        )

        client = SAPClient(config)
        assert client.config == config
        assert client.is_connected is False

    def test_sap_client_initialization_fails_with_invalid_config(self):
        """Should raise ValueError when config is missing required fields"""
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        with pytest.raises(ValueError, match="host is required"):
            SAPConfig(
                host="",
                client="100",
                user="testuser",
                password="testpass"
            )

    @pytest.mark.asyncio
    async def test_connect_to_sap_odata_service(self):
        """Should establish connection to SAP OData service"""
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass",
            connection_type="odata"
        )

        client = SAPClient(config)

        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = Mock(status_code=200, json=lambda: {"d": {"results": []}})

            await client.connect()

            assert client.is_connected is True
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_fails_with_invalid_credentials(self):
        """Should raise ConnectionError when credentials are invalid"""
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig
        from app.infrastructure.adapters.sap.exceptions import SAPAuthenticationError

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="invalid",
            password="invalid",
            connection_type="odata"
        )

        client = SAPClient(config)

        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = Mock(status_code=401)

            with pytest.raises(SAPAuthenticationError, match="Authentication failed"):
                await client.connect()

    @pytest.mark.asyncio
    async def test_disconnect_from_sap_service(self):
        """Should disconnect from SAP service and cleanup resources"""
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass",
            connection_type="odata"
        )

        client = SAPClient(config)

        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = Mock(status_code=200, json=lambda: {"d": {"results": []}})
            await client.connect()

        await client.disconnect()
        assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_execute_odata_query_successfully(self):
        """Should execute OData query and return parsed results"""
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass",
            connection_type="odata"
        )

        client = SAPClient(config)

        expected_data = {
            "d": {
                "results": [
                    {"MaterialNumber": "MAT001", "Description": "Test Material"}
                ]
            }
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_instance = AsyncMock()
            mock_client_class.return_value = mock_instance
            mock_instance.get.return_value = Mock(status_code=200, json=lambda: expected_data)

            await client.connect()
            result = await client.execute_query("/sap/opu/odata/sap/API_MATERIAL/MaterialSet")

            assert result == expected_data["d"]["results"]
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_execute_query_with_retry_on_timeout(self):
        """Should retry query execution on timeout errors"""
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig
        import httpx

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass",
            connection_type="odata",
            max_retries=3
        )

        client = SAPClient(config)

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_instance = AsyncMock()
            mock_client_class.return_value = mock_instance

            # First call for connect, then query calls: two timeouts, third succeeds
            mock_instance.get.side_effect = [
                Mock(status_code=200, json=lambda: {"d": {"results": []}}),  # connect
                httpx.TimeoutException("Request timeout"),  # query 1
                httpx.TimeoutException("Request timeout"),  # query 2
                Mock(status_code=200, json=lambda: {"d": {"results": []}})  # query 3
            ]

            await client.connect()
            result = await client.execute_query("/test/endpoint")

            assert result == []
            assert mock_instance.get.call_count == 4  # 1 connect + 3 query attempts

    @pytest.mark.asyncio
    async def test_execute_query_fails_after_max_retries(self):
        """Should raise exception after exceeding max retries"""
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig
        from app.infrastructure.adapters.sap.exceptions import SAPConnectionError
        import httpx

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass",
            connection_type="odata",
            max_retries=2
        )

        client = SAPClient(config)

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_instance = AsyncMock()
            mock_client_class.return_value = mock_instance

            # First call for connect, then all query calls timeout
            mock_instance.get.side_effect = [
                Mock(status_code=200, json=lambda: {"d": {"results": []}}),  # connect
                httpx.TimeoutException("Request timeout"),  # query attempt 1
                httpx.TimeoutException("Request timeout"),  # query attempt 2
                httpx.TimeoutException("Request timeout")   # query attempt 3
            ]

            await client.connect()

            with pytest.raises(SAPConnectionError, match="Max retries exceeded"):
                await client.execute_query("/test/endpoint")

            assert mock_instance.get.call_count == 4  # 1 connect + 3 query attempts (initial + 2 retries)

    @pytest.mark.asyncio
    async def test_post_data_to_sap_odata_service(self):
        """Should POST data to SAP OData service successfully"""
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass",
            connection_type="odata"
        )

        client = SAPClient(config)

        payload = {"MaterialNumber": "MAT001", "Description": "New Material"}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_instance = AsyncMock()
            mock_client_class.return_value = mock_instance
            mock_instance.get.return_value = Mock(status_code=200, json=lambda: {"d": {"results": []}})
            mock_instance.post.return_value = Mock(
                status_code=201,
                json=lambda: {"d": payload}
            )

            await client.connect()
            result = await client.execute_post("/sap/opu/odata/sap/API_MATERIAL/MaterialSet", payload)

            assert result == payload
            mock_instance.post.assert_called_once()
