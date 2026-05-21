import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from src.agents.supervisor import run_task_a
from src.agents.user_modeling import get_sample_users
from src.agents.review_simulation import find_product_by_description
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Twinn Review API starting...")
    from src.dataset_loader import ensure_dataset_available
    ensure_dataset_available()
    yield


app = FastAPI(
    title="Twinn Review API",
    description="Task A: LLM-powered review simulation agent",
    version="1.0.0",
    lifespan=lifespan
)


class ReviewRequest(BaseModel):
    user_id: str
    n_products: int = 3
    product_id: str = ""
    product_description: str = ""


class ReviewResponse(BaseModel):
    user_id: str
    profile: dict = {}
    simulated_reviews: list[dict] = []
    presented_reviews: list[str] = []
    metrics: dict = {}


@app.get("/")
def root():
    return {"status": "Twinn Review API is live 🎵", "version": "1.0.0"}


@app.post("/simulate", response_model=ReviewResponse)
def simulate_reviews(request: ReviewRequest):
    try:
        # Handle specific product input
        specific_product = None

        if request.product_id:
            from src.agents.review_simulation import get_product_context
            specific_product = get_product_context(request.product_id)
            if not specific_product:
                raise HTTPException(status_code=404, detail=f"Product ID {request.product_id} not found")

        elif request.product_description:
            specific_product = find_product_by_description(request.product_description)
            if not specific_product:
                raise HTTPException(status_code=404, detail=f"No product found matching: {request.product_description}")

        result = run_task_a(
            user_id=request.user_id,
            n_products=request.n_products,
            specific_product=specific_product
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return ReviewResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sample-users")
def sample_users(n: int = 5):
    users = get_sample_users(n)
    return {"users": users}


@app.get("/user/{user_id}")
def get_user_profile(user_id: str):
    from src.agents.user_modeling import get_or_build_profile
    profile = get_or_build_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


@app.get("/search-product")
def search_product(description: str):
    product = find_product_by_description(description)
    if not product:
        raise HTTPException(status_code=404, detail="No matching product found")
    return product


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
