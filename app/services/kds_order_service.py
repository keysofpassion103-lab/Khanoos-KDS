from typing import List, Dict
from fastapi import HTTPException, status
from app.database import supabase
from app.schemas.kds import (
    OrderCreate, OrderAddItems, OrderStatusUpdate,
    PaymentStatusUpdate, OrderPricingUpdate
)
from datetime import datetime, timezone, timedelta


def _get_ist_now() -> str:
    """Get current IST datetime as ISO string"""
    IST = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(IST).isoformat()


def _get_ist_start_of_day_utc() -> str:
    """Get start of today in IST, converted to UTC ISO string"""
    utc_now = datetime.now(timezone.utc)
    ist = utc_now + timedelta(hours=5, minutes=30)
    start_of_day_ist = ist.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_day_utc = start_of_day_ist - timedelta(hours=5, minutes=30)
    return start_of_day_utc.isoformat()


class KDSOrderService:

    @staticmethod
    async def get_today_orders(outlet_id: str) -> List[Dict]:
        """Get today's orders for an outlet (IST timezone)"""
        start_utc = _get_ist_start_of_day_utc()

        response = supabase.table("kds_orders").select("*").eq(
            "outlet_id", outlet_id
        ).gte(
            "created_at", start_utc
        ).order("created_at", desc=True).execute()

        # Load items for each order
        orders = response.data
        for order in orders:
            items_response = supabase.table("kds_order_items").select("*").eq(
                "order_id", order["id"]
            ).execute()
            order["items"] = items_response.data

        return orders

    @staticmethod
    async def get_order(order_id: str, outlet_id: str) -> Dict:
        """Get a single order with its items (scoped to outlet)"""
        response = supabase.table("kds_orders").select("*").eq(
            "id", order_id
        ).eq("outlet_id", outlet_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        order = response.data[0]

        # Load order items
        items_response = supabase.table("kds_order_items").select("*").eq(
            "order_id", order_id
        ).execute()
        order["items"] = items_response.data

        return order

    @staticmethod
    async def get_active_table_order(table_id: str, outlet_id: str) -> Dict:
        """Get the active order for a table (scoped to outlet)"""
        response = supabase.table("kds_orders").select("*").eq(
            "table_id", table_id
        ).eq("outlet_id", outlet_id).in_(
            "order_status", ["new", "preparing", "ready"]
        ).order("created_at", desc=True).limit(1).execute()

        if not response.data:
            return None

        order = response.data[0]

        # Load order items
        items_response = supabase.table("kds_order_items").select("*").eq(
            "order_id", order["id"]
        ).execute()
        order["items"] = items_response.data

        return order

    @staticmethod
    async def create_order(outlet_id: str, data: OrderCreate) -> Dict:
        """Create a new order with items"""
        try:
            # Get next order number via RPC
            order_number_response = supabase.rpc(
                "get_next_order_number",
                {"p_outlet_id": outlet_id}
            ).execute()

            order_number = str(order_number_response.data)

            # Calculate totals
            subtotal = sum(item.price * item.quantity for item in data.items)
            tax_amount = subtotal * (data.tax_percentage / 100)
            discount_amount = subtotal * (data.discount_percentage / 100)
            total_amount = subtotal + tax_amount - discount_amount

            # Build order data
            order_data = {
                "outlet_id": outlet_id,
                "order_number": order_number,
                "order_type": data.order_type,
                "table_number": data.table_number,
                "customer_name": data.customer_name,
                "customer_phone": data.customer_phone,
                "customer_address": data.customer_address,
                "notes": data.notes,
                "subtotal": subtotal,
                "tax_amount": tax_amount,
                "tax_percentage": data.tax_percentage,
                "discount_amount": discount_amount,
                "discount_percentage": data.discount_percentage,
                "total_amount": total_amount,
                "payment_status": data.payment_status or "pending",
                "payment_method": data.payment_method or "cash",
                "order_status": "new",
            }

            if data.order_type == "dine_in" and data.table_id:
                order_data["table_id"] = data.table_id

            # Insert order
            order_response = supabase.table("kds_orders").insert(
                order_data
            ).execute()

            if not order_response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create order"
                )

            order = order_response.data[0]
            order_id = order["id"]

            # Insert order items
            items_data = [{
                "order_id": order_id,
                "menu_item_id": item.menu_item_id,
                "item_name": item.item_name,
                "quantity": item.quantity,
                "price": item.price,
                "subtotal": item.price * item.quantity,
                "is_veg": item.is_veg,
                "special_instructions": item.special_instructions,
            } for item in data.items]

            supabase.table("kds_order_items").insert(items_data).execute()

            # Update table status and current_order_id if dine-in
            if data.order_type == "dine_in" and data.table_id:
                supabase.table("kds_tables").update(
                    {"status": "occupied", "current_order_id": order_id}
                ).eq("id", data.table_id).execute()

            # Return complete order
            order["items"] = items_data
            return order

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create order: {str(e)}"
            )

    @staticmethod
    async def add_items_to_order(order_id: str, outlet_id: str, data: OrderAddItems) -> Dict:
        """Add items to an existing order (scoped to outlet)"""
        # Verify order exists and belongs to outlet
        order_response = supabase.table("kds_orders").select("*").eq(
            "id", order_id
        ).eq("outlet_id", outlet_id).execute()

        if not order_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        order = order_response.data[0]

        # Insert new items
        items_data = [{
            "order_id": order_id,
            "menu_item_id": item.menu_item_id,
            "item_name": item.item_name,
            "quantity": item.quantity,
            "price": item.price,
            "subtotal": item.price * item.quantity,
            "is_veg": item.is_veg,
            "special_instructions": item.special_instructions,
        } for item in data.items]

        supabase.table("kds_order_items").insert(items_data).execute()

        # Recalculate totals (preserving existing discount)
        new_items_subtotal = sum(item.price * item.quantity for item in data.items)
        new_subtotal = float(order["subtotal"]) + new_items_subtotal
        tax_percentage = data.tax_percentage
        discount_percentage = float(order.get("discount_percentage", 0))
        new_tax_amount = new_subtotal * (tax_percentage / 100)
        new_discount_amount = new_subtotal * (discount_percentage / 100)
        new_total_amount = new_subtotal + new_tax_amount - new_discount_amount

        supabase.table("kds_orders").update({
            "subtotal": new_subtotal,
            "tax_amount": new_tax_amount,
            "discount_amount": new_discount_amount,
            "total_amount": new_total_amount,
        }).eq("id", order_id).execute()

        return await KDSOrderService.get_order(order_id, outlet_id)

    @staticmethod
    async def update_order_status(order_id: str, outlet_id: str, data: OrderStatusUpdate) -> Dict:
        """Update order status (scoped to outlet)"""
        update_data = {"order_status": data.order_status}

        if data.order_status == "completed":
            update_data["completed_at"] = _get_ist_now()

        response = supabase.table("kds_orders").update(
            update_data
        ).eq("id", order_id).eq("outlet_id", outlet_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        order = response.data[0]

        # Clear table's current_order_id when order is completed or cancelled
        if data.order_status in ("completed", "cancelled") and order.get("table_id"):
            supabase.table("kds_tables").update(
                {"status": "available", "current_order_id": None}
            ).eq("id", order["table_id"]).execute()

        return order

    @staticmethod
    async def update_payment_status(order_id: str, outlet_id: str, data: PaymentStatusUpdate) -> Dict:
        """Update payment status (scoped to outlet)"""
        update_data = {"payment_status": data.payment_status}

        if data.payment_method:
            update_data["payment_method"] = data.payment_method

        response = supabase.table("kds_orders").update(
            update_data
        ).eq("id", order_id).eq("outlet_id", outlet_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        return response.data[0]

    @staticmethod
    async def update_order_pricing(order_id: str, outlet_id: str, data: OrderPricingUpdate) -> Dict:
        """Update order pricing (scoped to outlet)"""
        tax_amount = data.subtotal * (data.tax_percentage / 100)
        discount_amount = data.subtotal * (data.discount_percentage / 100)
        total_amount = data.subtotal + tax_amount - discount_amount

        response = supabase.table("kds_orders").update({
            "subtotal": data.subtotal,
            "tax_percentage": data.tax_percentage,
            "tax_amount": tax_amount,
            "discount_percentage": data.discount_percentage,
            "discount_amount": discount_amount,
            "total_amount": total_amount,
        }).eq("id", order_id).eq("outlet_id", outlet_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        return response.data[0]

    @staticmethod
    async def cancel_order(order_id: str, outlet_id: str) -> Dict:
        """Cancel an order (scoped to outlet)"""
        response = supabase.table("kds_orders").update(
            {"order_status": "cancelled"}
        ).eq("id", order_id).eq("outlet_id", outlet_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        order = response.data[0]

        # Clear table's current_order_id when order is cancelled
        if order.get("table_id"):
            supabase.table("kds_tables").update(
                {"status": "available", "current_order_id": None}
            ).eq("id", order["table_id"]).execute()

        return order
