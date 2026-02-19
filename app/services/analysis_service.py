from typing import Dict, List, Optional
from fastapi import HTTPException, status
from app.database import supabase
from app.schemas.analysis import CurrencyDenominationCreate
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)


def _get_ist_now() -> str:
    """Get current IST datetime as ISO string"""
    IST = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(IST).isoformat()


def _to_ist_date_range_utc(date_str: str):
    """Convert IST date string to UTC start/end range"""
    dt = datetime.fromisoformat(date_str) if isinstance(date_str, str) else date_str
    start_of_day = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    # Convert IST to UTC
    start_utc = start_of_day - timedelta(hours=5, minutes=30)
    end_utc = end_of_day - timedelta(hours=5, minutes=30)
    return start_utc.isoformat(), end_utc.isoformat()


class AnalysisService:

    # =========================================================================
    # DAILY ANALYSIS
    # =========================================================================

    @staticmethod
    async def get_daily_analysis(outlet_id: str, date_str: str) -> Optional[Dict]:
        """Fetch existing daily analysis for a specific date"""
        try:
            response = supabase.table("kds_daily_analysis").select("*").eq(
                "outlet_id", outlet_id
            ).eq("analysis_date", date_str).maybe_single().execute()

            return response.data
        except Exception as e:
            logger.error(f"Error fetching daily analysis: {e}")
            return None

    @staticmethod
    async def generate_daily_analysis(outlet_id: str, date_str: str) -> Dict:
        """Generate daily analysis from order data for a specific date"""
        try:
            start_utc, end_utc = _to_ist_date_range_utc(date_str)

            # Fetch all orders for the day
            response = supabase.table("kds_orders").select("*").eq(
                "outlet_id", outlet_id
            ).gte("created_at", start_utc).lt("created_at", end_utc).execute()

            orders = response.data or []

            # Initialize counters
            dine_in_count = 0
            takeaway_count = 0
            delivery_count = 0
            dine_in_revenue = 0.0
            takeaway_revenue = 0.0
            delivery_revenue = 0.0
            cash_count = 0
            card_count = 0
            upi_count = 0
            razorpay_count = 0
            other_count = 0
            cash_revenue = 0.0
            card_revenue = 0.0
            upi_revenue = 0.0
            razorpay_revenue = 0.0
            other_revenue = 0.0
            cancelled_orders = 0
            total_tax = 0.0
            total_discount = 0.0

            for order in orders:
                order_status = (order.get("order_status") or "").lower()
                if order_status == "cancelled":
                    cancelled_orders += 1
                    continue

                amount = float(order.get("total_amount") or 0)
                order_type = (order.get("order_type") or "").lower()

                # Count by order type
                if order_type in ("dine-in", "dine_in"):
                    dine_in_count += 1
                    dine_in_revenue += amount
                elif order_type in ("takeaway", "pickup"):
                    takeaway_count += 1
                    takeaway_revenue += amount
                elif order_type == "delivery":
                    delivery_count += 1
                    delivery_revenue += amount

                # Count by payment method
                payment_method = (order.get("payment_method") or "").lower()
                if payment_method == "cash":
                    cash_count += 1
                    cash_revenue += amount
                elif payment_method in ("card", "debit card", "credit card"):
                    card_count += 1
                    card_revenue += amount
                elif payment_method == "upi":
                    upi_count += 1
                    upi_revenue += amount
                elif payment_method in ("razorpay", "online"):
                    razorpay_count += 1
                    razorpay_revenue += amount
                elif payment_method:
                    other_count += 1
                    other_revenue += amount

                total_tax += float(order.get("tax_amount") or 0)
                total_discount += float(order.get("discount_amount") or 0)

            total_orders = dine_in_count + takeaway_count + delivery_count
            total_revenue = dine_in_revenue + takeaway_revenue + delivery_revenue
            average_order_value = total_revenue / total_orders if total_orders > 0 else 0.0

            analysis_data = {
                "outlet_id": outlet_id,
                "analysis_date": date_str,
                "dine_in_count": dine_in_count,
                "takeaway_count": takeaway_count,
                "delivery_count": delivery_count,
                "total_orders": total_orders,
                "dine_in_revenue": round(dine_in_revenue, 2),
                "takeaway_revenue": round(takeaway_revenue, 2),
                "delivery_revenue": round(delivery_revenue, 2),
                "total_revenue": round(total_revenue, 2),
                "cash_revenue": round(cash_revenue, 2),
                "card_revenue": round(card_revenue, 2),
                "upi_revenue": round(upi_revenue, 2),
                "razorpay_revenue": round(razorpay_revenue, 2),
                "other_revenue": round(other_revenue, 2),
                "cash_count": cash_count,
                "card_count": card_count,
                "upi_count": upi_count,
                "razorpay_count": razorpay_count,
                "other_count": other_count,
                "cancelled_orders": cancelled_orders,
                "average_order_value": round(average_order_value, 2),
                "tax_collected": round(total_tax, 2),
                "discount_given": round(total_discount, 2),
                "updated_at": _get_ist_now(),
            }

            # Upsert (insert or update)
            result = supabase.table("kds_daily_analysis").upsert(
                analysis_data,
                on_conflict="outlet_id,analysis_date"
            ).execute()

            if result.data:
                logger.info(f"Generated analysis: {total_orders} orders, revenue={total_revenue}")
                return result.data[0]

            return analysis_data

        except Exception as e:
            logger.error(f"Error generating daily analysis: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate daily analysis: {str(e)}"
            )

    @staticmethod
    async def get_analysis_range(
        outlet_id: str, start_date: str, end_date: str
    ) -> List[Dict]:
        """Fetch analysis records for a date range"""
        try:
            response = supabase.table("kds_daily_analysis").select("*").eq(
                "outlet_id", outlet_id
            ).gte("analysis_date", start_date).lte(
                "analysis_date", end_date
            ).order("analysis_date", desc=True).execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching analysis range: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch analysis range: {str(e)}"
            )

    # =========================================================================
    # CURRENCY DENOMINATIONS
    # =========================================================================

    @staticmethod
    async def get_currency_denomination(
        outlet_id: str, date_str: str
    ) -> Optional[Dict]:
        """Fetch currency denomination for a specific date"""
        try:
            response = supabase.table("kds_currency_denominations").select("*").eq(
                "outlet_id", outlet_id
            ).eq("record_date", date_str).maybe_single().execute()

            return response.data
        except Exception as e:
            logger.error(f"Error fetching currency denomination: {e}")
            return None

    @staticmethod
    async def save_currency_denomination(
        outlet_id: str, data: CurrencyDenominationCreate
    ) -> Dict:
        """Save or update currency denomination"""
        try:
            # Calculate total
            total_amount = (
                data.notes_500 * 500.0 +
                data.notes_200 * 200.0 +
                data.notes_100 * 100.0 +
                data.notes_50 * 50.0 +
                data.notes_20 * 20.0 +
                data.notes_10 * 10.0 +
                data.coins_20 * 20.0 +
                data.coins_10 * 10.0 +
                data.coins_5 * 5.0 +
                data.coins_2 * 2.0 +
                data.coins_1 * 1.0
            )

            denomination_data = {
                "outlet_id": outlet_id,
                "record_date": data.record_date,
                "notes_500": data.notes_500,
                "notes_200": data.notes_200,
                "notes_100": data.notes_100,
                "notes_50": data.notes_50,
                "notes_20": data.notes_20,
                "notes_10": data.notes_10,
                "coins_20": data.coins_20,
                "coins_10": data.coins_10,
                "coins_5": data.coins_5,
                "coins_2": data.coins_2,
                "coins_1": data.coins_1,
                "total_amount": round(total_amount, 2),
                "updated_at": _get_ist_now(),
            }

            result = supabase.table("kds_currency_denominations").upsert(
                denomination_data,
                on_conflict="outlet_id,record_date"
            ).execute()

            if result.data:
                logger.info(f"Saved denomination: total={total_amount}")
                return result.data[0]

            return denomination_data

        except Exception as e:
            logger.error(f"Error saving currency denomination: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save currency denomination: {str(e)}"
            )

    @staticmethod
    async def get_denomination_range(
        outlet_id: str, start_date: str, end_date: str
    ) -> List[Dict]:
        """Fetch denomination records for a date range"""
        try:
            response = supabase.table("kds_currency_denominations").select("*").eq(
                "outlet_id", outlet_id
            ).gte("record_date", start_date).lte(
                "record_date", end_date
            ).order("record_date", desc=True).execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching denomination range: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch denomination range: {str(e)}"
            )