from fastapi import APIRouter, Depends, Query, status
from app.schemas.analysis import CurrencyDenominationCreate
from app.schemas.response import APIResponse
from app.services.analysis_service import AnalysisService
from app.auth.dependencies import get_current_outlet_user

router = APIRouter(prefix="/kds/analysis", tags=["KDS Analysis"])


# =============================================================================
# DAILY ANALYSIS ENDPOINTS
# =============================================================================

@router.get("/daily", response_model=APIResponse)
async def get_daily_analysis(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_current_outlet_user),
):
    """Get daily analysis for a specific date. Returns existing or generates new."""
    outlet_id = current_user["outlet_id"]

    # Try to fetch existing
    result = await AnalysisService.get_daily_analysis(outlet_id, date)
    if result:
        return APIResponse(success=True, data=result)

    # If not found, generate from orders
    result = await AnalysisService.generate_daily_analysis(outlet_id, date)
    return APIResponse(success=True, data=result)


@router.post("/daily/generate", response_model=APIResponse)
async def generate_daily_analysis(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_current_outlet_user),
):
    """Force regenerate daily analysis from order data"""
    result = await AnalysisService.generate_daily_analysis(
        current_user["outlet_id"], date
    )
    return APIResponse(
        success=True,
        message="Daily analysis generated successfully",
        data=result,
    )


@router.get("/daily/range", response_model=APIResponse)
async def get_analysis_range(
    start_date: str = Query(..., description="Start date YYYY-MM-DD"),
    end_date: str = Query(..., description="End date YYYY-MM-DD"),
    current_user: dict = Depends(get_current_outlet_user),
):
    """Get daily analysis for a date range"""
    result = await AnalysisService.get_analysis_range(
        current_user["outlet_id"], start_date, end_date
    )
    return APIResponse(success=True, data=result)


# =============================================================================
# CURRENCY DENOMINATION ENDPOINTS
# =============================================================================

@router.get("/denominations", response_model=APIResponse)
async def get_currency_denomination(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_current_outlet_user),
):
    """Get currency denomination for a specific date"""
    result = await AnalysisService.get_currency_denomination(
        current_user["outlet_id"], date
    )
    return APIResponse(success=True, data=result)


@router.post("/denominations", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def save_currency_denomination(
    data: CurrencyDenominationCreate,
    current_user: dict = Depends(get_current_outlet_user),
):
    """Save or update currency denomination for a date"""
    result = await AnalysisService.save_currency_denomination(
        current_user["outlet_id"], data
    )
    return APIResponse(
        success=True,
        message="Currency denomination saved successfully",
        data=result,
    )


@router.get("/denominations/range", response_model=APIResponse)
async def get_denomination_range(
    start_date: str = Query(..., description="Start date YYYY-MM-DD"),
    end_date: str = Query(..., description="End date YYYY-MM-DD"),
    current_user: dict = Depends(get_current_outlet_user),
):
    """Get currency denominations for a date range"""
    result = await AnalysisService.get_denomination_range(
        current_user["outlet_id"], start_date, end_date
    )
    return APIResponse(success=True, data=result)