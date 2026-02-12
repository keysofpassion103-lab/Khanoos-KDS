from fastapi import APIRouter, Depends, status
from app.schemas.kds import (
    OrderCreate, OrderAddItems, OrderStatusUpdate,
    PaymentStatusUpdate, OrderPricingUpdate
)
from app.schemas.response import APIResponse
from app.services.kds_order_service import KDSOrderService
from app.auth.dependencies import get_current_outlet_user

router = APIRouter(prefix="/kds/orders", tags=["KDS Orders"])


@router.get("", response_model=APIResponse)
async def get_today_orders(current_user: dict = Depends(get_current_outlet_user)):
    """Get today's orders for the current outlet"""
    result = await KDSOrderService.get_today_orders(current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.get("/{order_id}", response_model=APIResponse)
async def get_order(
    order_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Get a single order with items"""
    result = await KDSOrderService.get_order(order_id, current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.get("/table/{table_id}/active", response_model=APIResponse)
async def get_active_table_order(
    table_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Get the active order for a table"""
    result = await KDSOrderService.get_active_table_order(table_id, current_user["outlet_id"])
    return APIResponse(success=True, data=result)


@router.post("", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Create a new order with items"""
    result = await KDSOrderService.create_order(current_user["outlet_id"], data)
    return APIResponse(success=True, message="Order created successfully", data=result)


@router.post("/{order_id}/items", response_model=APIResponse)
async def add_items_to_order(
    order_id: str,
    data: OrderAddItems,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Add items to an existing order"""
    result = await KDSOrderService.add_items_to_order(order_id, current_user["outlet_id"], data)
    return APIResponse(success=True, message="Items added successfully", data=result)


@router.patch("/{order_id}/status", response_model=APIResponse)
async def update_order_status(
    order_id: str,
    data: OrderStatusUpdate,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Update order status"""
    result = await KDSOrderService.update_order_status(order_id, current_user["outlet_id"], data)
    return APIResponse(success=True, message="Order status updated", data=result)


@router.patch("/{order_id}/payment", response_model=APIResponse)
async def update_payment_status(
    order_id: str,
    data: PaymentStatusUpdate,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Update payment status"""
    result = await KDSOrderService.update_payment_status(order_id, current_user["outlet_id"], data)
    return APIResponse(success=True, message="Payment status updated", data=result)


@router.patch("/{order_id}/pricing", response_model=APIResponse)
async def update_order_pricing(
    order_id: str,
    data: OrderPricingUpdate,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Update order pricing (tax, discount, totals)"""
    result = await KDSOrderService.update_order_pricing(order_id, current_user["outlet_id"], data)
    return APIResponse(success=True, message="Order pricing updated", data=result)


@router.post("/{order_id}/cancel", response_model=APIResponse)
async def cancel_order(
    order_id: str,
    current_user: dict = Depends(get_current_outlet_user)
):
    """Cancel an order"""
    result = await KDSOrderService.cancel_order(order_id, current_user["outlet_id"])
    return APIResponse(success=True, message="Order cancelled", data=result)
