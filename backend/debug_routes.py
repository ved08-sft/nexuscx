"""
Debug script to see what routes are available in the FastAPI app.
"""
from app.main import app

def extract_paths_from_routes(routes, prefix=""):
    """Recursively extract all paths from routes, handling included routers."""
    paths = []
    for route in routes:
        # Check if this is an IncludedRouter
        if hasattr(route, 'original_router') and hasattr(route, 'include_context'):
            # This is an included router
            subprefix = prefix + route.include_context.prefix
            subpaths = extract_paths_from_routes(route.original_router.routes, subprefix)
            paths.extend(subpaths)
        elif hasattr(route, 'path'):
            # This is a regular route
            paths.append(prefix + route.path)
    return paths

print("Available routes in the app:")
all_paths = extract_paths_from_routes(app.routes)
for path in sorted(all_paths):
    print(f"  {path}")

print(f"\nTotal routes: {len(all_paths)}")