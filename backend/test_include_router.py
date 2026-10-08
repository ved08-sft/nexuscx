"""
Test to verify that include_router works correctly.
"""
from fastapi import APIRouter

# Create a test router
test_router = APIRouter()

@test_router.get("/test")
async def test_endpoint():
    return {"message": "test"}

print(f"Test router: {test_router}")
print(f"Test router routes before inclusion: {[r.path for r in test_router.routes if hasattr(r, 'path')]}")

# Create main router
main_router = APIRouter()
print(f"Main router before inclusion: {main_router}")
print(f"Main router routes before inclusion: {[r.path for r in main_router.routes if hasattr(r, 'path')]}")

# Include the test router
print(f"Including test router with prefix '/test'")
main_router.include_router(test_router, prefix="/test")
print(f"Main router after inclusion: {main_router}")
print(f"Main router routes after inclusion: {[r.path for r in main_router.routes if hasattr(r, 'path')]}")

# Let's see what attributes the _IncludedRouter has
print(f"Main router routes after inclusion: {main_router.routes}")
if main_router.routes:
    route0 = main_router.routes[0]
    print(f"First route: {route0}")
    print(f"Type of first route: {type(route0)}")
    print(f"Attributes of first route: {[attr for attr in dir(route0) if not attr.startswith('_')]}")
    # Check for specific attributes we might need
    for attr in ['router', 'prefix', 'paths']:
        if hasattr(route0, attr):
            print(f"  {attr}: {getattr(route0, attr)}")

def extract_paths_from_routes(routes, prefix=""):
    """Recursively extract all paths from routes, handling included routers."""
    print(f"  extract_paths_from_routes called with {len(routes)} routes, prefix='{prefix}'")
    paths = []
    for i, route in enumerate(routes):
        print(f"    Route {i}: {type(route)}")
        # Check if this is an IncludedRouter
        if hasattr(route, 'original_router') and hasattr(route, 'include_context'):
            # This is an included router
            print(f"      This is an included router")
            print(f"        original_router: {route.original_router}")
            print(f"        include_context.prefix: {route.include_context.prefix}")
            # Get the paths from the included router
            subprefix = prefix + route.include_context.prefix
            print(f"        Subprefix: {subprefix}")
            subpaths = extract_paths_from_routes(route.original_router.routes, subprefix)
            print(f"        Got subpaths: {subpaths}")
            paths.extend(subpaths)
        elif hasattr(route, 'path'):
            # This is a regular route
            full_path = prefix + route.path
            print(f"      This is a regular route with path='{route.path}', full path: '{full_path}'")
            paths.append(full_path)
        else:
            print(f"      This route has neither expected attributes for path extraction")
    print(f"  extract_paths_from_routes returning: {paths}")
    return paths

print(f"Main router routes after inclusion: {extract_paths_from_routes(main_router.routes)}")

# Also check if we can access the routes property correctly
print(f"Main router routes (detailed):")
all_paths = extract_paths_from_routes(main_router.routes)
print(f"All paths: {all_paths}")

# Test with prefixes
print(f"\nTesting with prefix:")
main_router2 = APIRouter()
print(f"Main router2 before inclusion: {main_router2}")
main_router2.include_router(test_router, prefix="/api/v1")
print(f"Main router2 after inclusion: {main_router2}")
all_paths2 = extract_paths_from_routes(main_router2.routes)
print(f"All paths with prefix: {all_paths2}")