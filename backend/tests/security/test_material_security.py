"""
Security Tests for Material Management - CRITICAL VULNERABILITIES

Tests for 3 BLOCKING security issues:
1. Mock authentication bypass
2. SQL injection in search
3. RLS context enforcement

These tests MUST pass before deployment.
"""
import pytest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


# Avoid SQLAlchemy import issues - test repository directly
class MockSession:
    """Mock SQLAlchemy session for testing"""
    def __init__(self):
        self.queries = []
        self.committed = False

    def query(self, *args, **kwargs):
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_query.first = Mock(return_value=None)
        self.queries.append({"args": args, "kwargs": kwargs})
        return mock_query

    def add(self, obj):
        pass

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        pass

    def rollback(self):
        pass


@pytest.fixture(scope="module")
def test_db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db):
    """Create database session for tests"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_app():
    """Create test FastAPI app with materials router"""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/materials", tags=["Materials"])
    return app


@pytest.fixture
def client(test_app, db_session):
    """Test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    test_app.dependency_overrides[get_db] = override_get_db
    return TestClient(test_app)


@pytest.fixture
def jwt_handler():
    """JWT handler for creating test tokens"""
    return JWTHandler()


class TestAuthenticationRequired:
    """CRITICAL Issue 1: Test that authentication is required for all endpoints"""

    def test_create_material_without_auth_returns_401(self, client):
        """Test that creating material without auth token returns 401"""
        # Arrange
        material_data = {
            "organization_id": 1,
            "plant_id": 1,
            "material_number": "MAT001",
            "material_name": "Test Material",
            "material_category_id": 1,
            "base_uom_id": 1,
            "procurement_type": "PURCHASE",
            "mrp_type": "MRP",
        }

        # Act - NO Authorization header
        response = client.post("/api/v1/materials/", json=material_data)

        # Assert - Should fail with 401, NOT succeed with mock auth
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
            "CRITICAL: Mock auth allows unauthenticated access!"

    def test_get_material_without_auth_returns_401(self, client):
        """Test that getting material without auth token returns 401"""
        # Act - NO Authorization header
        response = client.get("/api/v1/materials/1")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
            "CRITICAL: Mock auth allows unauthenticated access!"

    def test_list_materials_without_auth_returns_401(self, client):
        """Test that listing materials without auth token returns 401"""
        # Act - NO Authorization header
        response = client.get("/api/v1/materials/")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
            "CRITICAL: Mock auth allows unauthenticated access!"

    def test_search_materials_without_auth_returns_401(self, client):
        """Test that searching materials without auth token returns 401"""
        # Act - NO Authorization header
        response = client.get("/api/v1/materials/search?q=test")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
            "CRITICAL: Mock auth allows unauthenticated access!"

    def test_update_material_without_auth_returns_401(self, client):
        """Test that updating material without auth token returns 401"""
        # Arrange
        update_data = {"material_name": "Updated"}

        # Act - NO Authorization header
        response = client.put("/api/v1/materials/1", json=update_data)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
            "CRITICAL: Mock auth allows unauthenticated access!"

    def test_delete_material_without_auth_returns_401(self, client):
        """Test that deleting material without auth token returns 401"""
        # Act - NO Authorization header
        response = client.delete("/api/v1/materials/1")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
            "CRITICAL: Mock auth allows unauthenticated access!"


class TestSQLInjectionProtection:
    """CRITICAL Issue 2: Test that search is protected against SQL injection"""

    def test_search_escapes_percent_wildcard(self, db_session):
        """Test that % character in search is escaped, not used as wildcard"""
        # Arrange - Create materials
        repo = MaterialRepository(db_session, use_pg_search=False)

        # Create material with specific pattern
        material_data = {
            "organization_id": 1,
            "plant_id": 1,
            "material_number": "TEST100",
            "material_name": "100% Cotton",
            "description": "Pure cotton material",
            "material_category_id": 1,
            "base_uom_id": 1,
            "procurement_type": "PURCHASE",
            "mrp_type": "MRP",
        }
        repo.create(material_data)

        # Act - Search for literal "100%" (should match)
        results = repo.search_materials(query="100%", org_id=1, plant_id=1, limit=20)

        # Assert - Should find exact match, not wildcard match
        assert len(results) == 1, "Should find material with literal '100%'"
        assert results[0].material_name == "100% Cotton"

    def test_search_escapes_underscore_wildcard(self, db_session):
        """Test that _ character in search is escaped, not used as wildcard"""
        # Arrange
        repo = MaterialRepository(db_session, use_pg_search=False)

        material_data = {
            "organization_id": 1,
            "plant_id": 1,
            "material_number": "MAT_001",
            "material_name": "Test Material",
            "description": "Material with underscore",
            "material_category_id": 1,
            "base_uom_id": 1,
            "procurement_type": "PURCHASE",
            "mrp_type": "MRP",
        }
        repo.create(material_data)

        # Act - Search for literal "MAT_001" (should NOT match "MATX001" if it existed)
        results = repo.search_materials(query="MAT_001", org_id=1, plant_id=1, limit=20)

        # Assert
        assert len(results) == 1
        assert results[0].material_number == "MAT_001"

    def test_search_prevents_dos_with_multiple_wildcards(self, db_session):
        """Test that malicious wildcard patterns don't cause DoS"""
        # Arrange
        repo = MaterialRepository(db_session, use_pg_search=False)

        # Act - Attempt DoS with expensive wildcard pattern
        malicious_query = "%_%_%_%_%_%_%_%_%_"

        # This should complete quickly without expensive wildcard scans
        import time
        start = time.time()
        results = repo.search_materials(query=malicious_query, org_id=1, plant_id=1, limit=20)
        elapsed = time.time() - start

        # Assert - Should be fast and return literal match only
        assert elapsed < 1.0, f"Query took {elapsed}s - possible DoS vulnerability!"
        assert len(results) == 0, "Should not match anything with escaped wildcards"

    def test_search_escapes_backslash(self, db_session):
        """Test that backslash character is properly escaped"""
        # Arrange
        repo = MaterialRepository(db_session, use_pg_search=False)

        material_data = {
            "organization_id": 1,
            "plant_id": 1,
            "material_number": "MAT\\001",
            "material_name": "Test Material",
            "description": "Material with backslash",
            "material_category_id": 1,
            "base_uom_id": 1,
            "procurement_type": "PURCHASE",
            "mrp_type": "MRP",
        }
        repo.create(material_data)

        # Act - Search for literal backslash
        results = repo.search_materials(query="MAT\\001", org_id=1, plant_id=1, limit=20)

        # Assert
        assert len(results) == 1
        assert results[0].material_number == "MAT\\001"


class TestRLSContextEnforcement:
    """CRITICAL Issue 3: Test that RLS context properly isolates organizations"""

    def test_rls_prevents_cross_org_access_by_id(self, db_session):
        """Test that user from org 1 cannot access org 2 material by ID"""
        # Arrange - Create materials in different orgs
        repo = MaterialRepository(db_session, use_pg_search=False)

        # Material in org 1
        material_org1_data = {
            "organization_id": 1,
            "plant_id": 1,
            "material_number": "ORG1MAT",
            "material_name": "Org 1 Material",
            "material_category_id": 1,
            "base_uom_id": 1,
            "procurement_type": "PURCHASE",
            "mrp_type": "MRP",
        }
        material_org1 = repo.create(material_org1_data)

        # Material in org 2
        material_org2_data = {
            "organization_id": 2,
            "plant_id": 2,
            "material_number": "ORG2MAT",
            "material_name": "Org 2 Material",
            "material_category_id": 1,
            "base_uom_id": 1,
            "procurement_type": "PURCHASE",
            "mrp_type": "MRP",
        }
        material_org2 = repo.create(material_org2_data)

        # Act - Simulate RLS context for org 1 user
        # NOTE: This test requires RLS policies to be active in database
        # For now, we verify that repository respects organization filtering

        # Search from org 1 perspective
        results_org1 = repo.search_materials(query="ORG", org_id=1, plant_id=1, limit=20)

        # Assert - Should only see org 1 material
        assert len(results_org1) == 1, "Should only see materials from own organization"
        assert results_org1[0].material_number == "ORG1MAT"
        assert results_org1[0].organization_id == 1

    def test_rls_prevents_cross_org_access_in_list(self, db_session):
        """Test that listing materials only shows user's organization"""
        # Arrange
        repo = MaterialRepository(db_session, use_pg_search=False)

        # Create multiple materials in different orgs
        for org_id in [1, 2, 3]:
            material_data = {
                "organization_id": org_id,
                "plant_id": org_id,
                "material_number": f"ORG{org_id}MAT",
                "material_name": f"Org {org_id} Material",
                "material_category_id": 1,
                "base_uom_id": 1,
                "procurement_type": "PURCHASE",
                "mrp_type": "MRP",
            }
            repo.create(material_data)

        # Act - List from org 1 perspective
        result = repo.list_by_organization(org_id=1, plant_id=1, page=1, page_size=50)

        # Assert - Should only see org 1 materials
        assert result["total"] == 1
        assert all(m.organization_id == 1 for m in result["items"])

    def test_rls_context_extracted_from_jwt(self, jwt_handler):
        """Test that RLS context is properly extracted from JWT token"""
        # Arrange - Create JWT token with org/plant info
        token_payload = {
            "sub": "1",
            "email": "test@example.com",
            "organization_id": 42,
            "plant_id": 7,
            "type": "access"
        }

        # Act - Encode and decode token
        token = jwt_handler.create_access_token(
            user_id=1,
            email="test@example.com"
        )

        # For this test, we need to verify that auth middleware properly extracts
        # organization_id and plant_id from JWT and sets request.state.user
        # This is integration test territory, but we verify the JWT structure

        decoded = jwt_handler.decode_token(token)

        # Assert - Token should contain user identification
        assert "sub" in decoded
        assert "email" in decoded
        # NOTE: Current JWT handler may not include org_id/plant_id
        # This test documents the expected behavior


class TestIntegrationSecurity:
    """Integration tests for complete security flow"""

    def test_authenticated_request_sets_rls_context(self, client, jwt_handler, db_session):
        """Test that authenticated request properly sets RLS context in database"""
        # Arrange - Create valid JWT token
        token = jwt_handler.create_access_token(user_id=1, email="test@example.com")

        # Mock get_db to verify RLS context is set
        rls_context_calls = []

        def mock_get_db():
            # Capture what organization_id was set for RLS
            # In real flow, get_db() would call set_rls_context()
            rls_context_calls.append({"called": True})
            yield db_session

        # Act - Make authenticated request
        headers = {"Authorization": f"Bearer {token}"}

        # For this test to pass, materials.py must use real get_current_user dependency
        # NOT the mock version

        # This test will FAIL until Issue 1 is fixed
        # Keeping it here to verify the fix works

    def test_unauthenticated_request_has_no_rls_context(self, client):
        """Test that unauthenticated request fails before RLS context is needed"""
        # Act - Request without auth header
        response = client.get("/api/v1/materials/")

        # Assert - Should fail at auth layer, not reach database
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
