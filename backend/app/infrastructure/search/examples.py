"""
Example usage of PgSearchService for material search.

Demonstrates BM25 search, fallback mode, and configuration.
"""
from typing import List
from app.infrastructure.search import PgSearchService, SearchResult, SearchConfig
from app.core.database import SessionLocal


def example_basic_search():
    """Example: Basic material search with BM25 ranking."""
    print("\n=== Example 1: Basic BM25 Search ===")

    db = SessionLocal()
    try:
        # Configure for production (pg_search enabled)
        config = SearchConfig(use_pg_search=True, default_limit=10)
        search_service = PgSearchService(db, config)

        # Search for materials
        results = search_service.search_materials(
            query="steel plate",
            organization_id=1,
            plant_id=1,
            limit=10
        )

        print(f"Found {len(results)} materials:")
        for result in results:
            print(
                f"  {result.material_number}: {result.material_name} "
                f"(score: {result.score:.2f})"
            )

    finally:
        db.close()


def example_fallback_mode():
    """Example: Fallback to LIKE queries for testing."""
    print("\n=== Example 2: LIKE Fallback Mode ===")

    db = SessionLocal()
    try:
        # Configure for testing (pg_search disabled)
        config = SearchConfig(use_pg_search=False)
        search_service = PgSearchService(db, config)

        # Search uses LIKE instead of BM25
        results = search_service.search_materials(
            query="steel",
            organization_id=1,
            limit=5
        )

        print(f"Found {len(results)} materials (LIKE search):")
        for result in results:
            print(f"  {result.material_number}: {result.material_name}")

    finally:
        db.close()


def example_filtered_search():
    """Example: Search with organization and plant filtering."""
    print("\n=== Example 3: Filtered Search ===")

    db = SessionLocal()
    try:
        config = SearchConfig(use_pg_search=True)
        search_service = PgSearchService(db, config)

        # Search within specific plant
        results = search_service.search_materials(
            query="bearing",
            organization_id=1,
            plant_id=2,  # Specific plant
            limit=20
        )

        print(f"Found {len(results)} bearings in Plant 2:")
        for result in results:
            print(
                f"  {result.material_number}: {result.material_name} "
                f"(Plant: {result.plant_id}, Score: {result.score})"
            )

    finally:
        db.close()


def example_custom_config():
    """Example: Custom BM25 configuration."""
    print("\n=== Example 4: Custom BM25 Configuration ===")

    db = SessionLocal()
    try:
        # Custom BM25 parameters for specific use case
        config = SearchConfig(
            use_pg_search=True,
            default_limit=50,
            max_limit=200,
            bm25_k1=1.5,  # Higher term frequency weight
            bm25_b=0.5,   # Less length normalization
            enable_fuzzy=True,
            fuzzy_distance=1
        )
        search_service = PgSearchService(db, config)

        results = search_service.search_materials(
            query="stainless",
            organization_id=1
        )

        print(f"Found {len(results)} stainless materials:")
        for result in results[:5]:  # Show top 5
            print(
                f"  {result.material_number}: {result.material_name} "
                f"(Score: {result.score:.2f})"
            )

    finally:
        db.close()


def example_search_result_usage():
    """Example: Using SearchResult data transfer object."""
    print("\n=== Example 5: SearchResult DTO Usage ===")

    db = SessionLocal()
    try:
        config = SearchConfig(use_pg_search=True)
        search_service = PgSearchService(db, config)

        results = search_service.search_materials(
            query="motor",
            organization_id=1,
            limit=3
        )

        for result in results:
            print(f"\nMaterial: {result.material_number}")
            print(f"  Name: {result.material_name}")
            print(f"  Description: {result.description}")
            print(f"  Category ID: {result.material_category_id}")
            print(f"  Procurement: {result.procurement_type}")
            print(f"  MRP Type: {result.mrp_type}")
            print(f"  Safety Stock: {result.safety_stock}")
            print(f"  Reorder Point: {result.reorder_point}")
            print(f"  Lead Time: {result.lead_time_days} days")
            print(f"  Active: {result.is_active}")
            print(f"  BM25 Score: {result.score:.2f}")

    finally:
        db.close()


def example_empty_results():
    """Example: Handling empty search results."""
    print("\n=== Example 6: Empty Results Handling ===")

    db = SessionLocal()
    try:
        config = SearchConfig(use_pg_search=True)
        search_service = PgSearchService(db, config)

        # Search with no matches
        results = search_service.search_materials(
            query="nonexistent_material_xyz123",
            organization_id=1
        )

        if not results:
            print("No materials found matching the query.")
        else:
            print(f"Found {len(results)} materials")

        # Empty query
        results = search_service.search_materials(
            query="",
            organization_id=1
        )
        print(f"Empty query returned: {len(results)} results")

        # Whitespace query
        results = search_service.search_materials(
            query="   ",
            organization_id=1
        )
        print(f"Whitespace query returned: {len(results)} results")

    finally:
        db.close()


def example_integration_with_application_service():
    """Example: Integration with existing MaterialSearchService."""
    print("\n=== Example 7: Integration Pattern ===")

    from app.application.services.material_search_service import MaterialSearchService
    from app.infrastructure.repositories.material_repository import MaterialRepository

    db = SessionLocal()
    try:
        # Initialize infrastructure layer
        material_repo = MaterialRepository(db, use_pg_search=True)

        # Initialize application service
        search_service = MaterialSearchService(material_repo)

        # Application layer handles filtering and formatting
        results = search_service.search(
            query="bolt",
            organization_id=1,
            plant_id=1,
            filters={"is_active": True, "procurement_type": "purchase"},
            limit=10
        )

        print(f"Found {len(results)} active purchased bolts:")
        for result in results[:3]:
            print(f"  {result['material_number']}: {result['material_name']}")

    finally:
        db.close()


def example_performance_comparison():
    """Example: Performance comparison between BM25 and LIKE."""
    import time

    print("\n=== Example 8: Performance Comparison ===")

    db = SessionLocal()
    try:
        query = "steel"
        org_id = 1
        limit = 100

        # BM25 search
        config_bm25 = SearchConfig(use_pg_search=True)
        service_bm25 = PgSearchService(db, config_bm25)

        start = time.time()
        results_bm25 = service_bm25.search_materials(query, org_id, limit=limit)
        time_bm25 = (time.time() - start) * 1000

        # LIKE search
        config_like = SearchConfig(use_pg_search=False)
        service_like = PgSearchService(db, config_like)

        start = time.time()
        results_like = service_like.search_materials(query, org_id, limit=limit)
        time_like = (time.time() - start) * 1000

        print(f"BM25 Search: {len(results_bm25)} results in {time_bm25:.2f}ms")
        print(f"LIKE Search: {len(results_like)} results in {time_like:.2f}ms")
        print(f"Speedup: {time_like/time_bm25:.2f}x faster with BM25")

    finally:
        db.close()


if __name__ == "__main__":
    """
    Run all examples (requires database with test data).

    Usage:
        python -m app.infrastructure.search.examples
    """
    examples = [
        example_basic_search,
        example_fallback_mode,
        example_filtered_search,
        example_custom_config,
        example_search_result_usage,
        example_empty_results,
        # example_integration_with_application_service,  # Requires full setup
        # example_performance_comparison,  # Requires data
    ]

    print("PgSearchService - Usage Examples")
    print("=" * 60)

    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\nError in {example_func.__name__}: {e}")

    print("\n" + "=" * 60)
    print("Examples completed!")
