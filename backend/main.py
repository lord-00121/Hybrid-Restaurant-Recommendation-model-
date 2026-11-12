import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import db
from routes.auth import router as auth_router
from routes.ratings import router as ratings_router
from routes.recommendations import router as recommendations_router
from routes.restaurants import router as restaurants_router
from routes.interactions import router as interactions_router
from routes.stats import router as stats_router
from routes.evaluation import router as evaluation_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the FastAPI application."""
    # Create indexes on startup
    try:
        await db.users.create_index("email", unique=True)
        await db.restaurants.create_index("name")
        await db.restaurants.create_index("cuisine")
        await db.restaurants.create_index("location.area")
        await db.ratings.create_index([("user_id", 1), ("restaurant_id", 1)], unique=True)
        await db.interactions.create_index("user_id")
        await db.interactions.create_index("restaurant_id")
        print("MongoDB indexes verified successfully.")
    except Exception as e:
        print(f"Notice: Could not initialize MongoDB indexes during startup ({e}).")

    yield

    # Clean up resources on shutdown if needed
    print("Application shutdown complete.")


app = FastAPI(
    title="Hybrid Restaurant Recommendation System",
    description="A production-grade recommendation engine blending content-based and collaborative filtering.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for development frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers under /api prefix
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(restaurants_router, prefix="/api/restaurants", tags=["restaurants"])
app.include_router(ratings_router, prefix="/api/ratings", tags=["ratings"])
app.include_router(recommendations_router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(interactions_router, prefix="/api/interactions", tags=["interactions"])
app.include_router(stats_router, prefix="/api/stats", tags=["stats"])
app.include_router(evaluation_router, prefix="/api/evaluation", tags=["evaluation"])


@app.get("/", tags=["health"])
async def root():
    """Root status endpoint."""
    return {"status": "ok", "app": "Hybrid Restaurant Recommender"}


@app.get("/api", tags=["health"])
async def api_root():
    """API health status endpoint."""
    return {"status": "ok", "message": "Hybrid Restaurant Recommender API is active"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
