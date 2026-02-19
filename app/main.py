from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.routers import (
    admin_auth, plan_types, chain_outlets, single_outlets,
    licenses, subscriptions, activity_logs, app_auth,
    kds_menu, kds_orders, kds_kots, kds_sections, kds_inventory,
    kds_analysis,
)
import logging

# Force INFO level so all application logs appear in Render/production logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)

# Configure logging
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Khanoos Outlet Licensing System API",
    description="Backend API for Outlet License Management and Subscription System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Format validation errors to be user-friendly
    errors = []
    for error in exc.errors():
        error_detail = {
            "field": " -> ".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg", "Validation error"),
            "type": error.get("type", "value_error")
        }
        errors.append(error_detail)

    # Log validation errors so they appear in Render logs
    logger.warning(f"[VALIDATION ERROR] {request.method} {request.url.path} -> {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": errors
            }
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions from Pydantic validators"""
    logger.warning(f"ValueError in request to {request.url.path}: {str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(exc)
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Log the error for debugging
    logger.error(f"Unhandled exception in {request.url.path}: {type(exc).__name__}: {str(exc)}", exc_info=True)

    # Get error message safely
    error_message = "Internal server error"
    if settings.DEBUG:
        try:
            error_message = str(exc)
        except Exception:
            error_message = repr(exc)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": error_message,
                "type": type(exc).__name__ if settings.DEBUG else None
            }
        }
    )

# Startup validation
@app.on_event("startup")
async def startup_event():
    settings.validate_required()
    logger.warning("✅ Khanoos API v1.1 started — logging active")

# Health check and info endpoints
@app.get("/")
async def root():
    return {
        "message": "Khanoos Outlet Licensing System API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "features": [
            "Outlet license management",
            "Chain and single outlet support",
            "Subscription plan management",
            "Activity audit logging",
            "KDS - Menu management",
            "KDS - Order & KOT management",
            "KDS - Sections & Tables",
            "KDS - Inventory & Recipe management",
            "KDS - Smart Analysis & Currency Denominations",
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "api_version": "1.0.0"
    }

# Include routers
app.include_router(admin_auth.router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(plan_types.router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(chain_outlets.router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(single_outlets.router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(licenses.router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(subscriptions.router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(activity_logs.router, prefix=f"/api/{settings.API_VERSION}")

# App Auth (POS/Kitchen app endpoints)
app.include_router(app_auth.router, prefix=f"/api/{settings.API_VERSION}")

# KDS Routers (Outlet user authenticated)
app.include_router(kds_menu.router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(kds_orders.router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(kds_kots.router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(kds_sections.router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(kds_inventory.router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(kds_analysis.router, prefix=f"/api/{settings.API_VERSION}")

# if __name__ == "__main__":
#     # import uvicorn
#     # uvicorn.run(
#     #     "app.main:app",
#     #     host="0.0.0.0",
#     #     port=8000,
#     #     reload=True,
#     #     log_level="info"
#      )
