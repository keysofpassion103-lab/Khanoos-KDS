from typing import Dict, List, Optional
from fastapi import HTTPException, status
from app.database import get_fresh_supabase_client, get_anon_supabase_client, supabase
from app.schemas.chain_owner import ChainOwnerSignupRequest, ChainOwnerLoginRequest
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)


def _to_ist_date_range_utc(date_str: str):
    """Convert IST date string to UTC start/end range"""
    dt = datetime.fromisoformat(date_str) if isinstance(date_str, str) else date_str
    start_of_day = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    start_utc = start_of_day - timedelta(hours=5, minutes=30)
    end_utc = end_of_day - timedelta(hours=5, minutes=30)
    return start_utc.isoformat(), end_utc.isoformat()


class ChainOwnerService:

    @staticmethod
    async def signup(data: ChainOwnerSignupRequest) -> Dict:
        """Register a chain owner using their master license key"""
        try:
            logger.info(f"[CHAIN SIGNUP] Starting signup for: {data.email}")

            db = get_fresh_supabase_client()

            # 1. Verify master license key exists in chain_outlets
            chain_resp = db.table("chain_outlets").select(
                "id, chain_name, master_admin_name, master_admin_email, is_active"
            ).eq("master_license_key", data.master_license_key.strip()).execute()

            if not chain_resp.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid master license key"
                )

            chain = chain_resp.data[0]
            chain_id = chain["id"]
            chain_name = chain["chain_name"]

            logger.info(f"[CHAIN SIGNUP] Found chain: {chain_name} ({chain_id})")

            # 2. Create user in Supabase Auth
            auth_client = get_fresh_supabase_client()
            try:
                auth_response = auth_client.auth.admin.create_user({
                    "email": data.email,
                    "password": data.password,
                    "email_confirm": True,
                    "user_metadata": {
                        "full_name": data.full_name,
                        "user_type": "chain_owner",
                        "chain_id": chain_id
                    }
                })
            except Exception as auth_err:
                err_msg = str(auth_err).lower()
                if "already registered" in err_msg or "already exists" in err_msg or "email address is already" in err_msg:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="An account with this email already exists. Please login instead."
                    )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create account: {str(auth_err)}"
                )

            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create chain owner account"
                )

            # 3. Mark master key as used and activate chain
            fresh = get_fresh_supabase_client()
            fresh.table("chain_outlets").update({
                "master_key_used": True,
                "is_active": True,
                "auth_user_id": str(auth_response.user.id)
            }).eq("id", chain_id).execute()

            logger.info(f"[CHAIN SIGNUP] Success for: {data.email}")

            return {
                "success": True,
                "message": "Chain owner account created. You can now login.",
                "user": {
                    "id": str(auth_response.user.id),
                    "email": data.email,
                    "full_name": data.full_name
                },
                "chain": {
                    "id": chain_id,
                    "chain_name": chain_name,
                    "is_active": True
                }
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Chain signup error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Chain owner signup failed: {str(e)}"
            )

    @staticmethod
    async def login(data: ChainOwnerLoginRequest) -> Dict:
        """Login chain owner via Supabase Auth"""
        try:
            logger.info(f"[CHAIN LOGIN] Attempting login for: {data.email}")

            # 1. Sign in with Supabase Auth
            anon_client = get_anon_supabase_client()
            auth_response = anon_client.auth.sign_in_with_password({
                "email": data.email,
                "password": data.password
            })

            if not auth_response.user or not auth_response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )

            user = auth_response.user
            user_type = user.user_metadata.get("user_type", "") if user.user_metadata else ""

            if user_type != "chain_owner":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This account is not a chain owner account."
                )

            chain_id = user.user_metadata.get("chain_id") if user.user_metadata else None
            if not chain_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No chain linked to this account."
                )

            # 2. Verify chain exists and is active
            db = get_fresh_supabase_client()
            chain_resp = db.table("chain_outlets").select("*").eq(
                "id", chain_id
            ).execute()

            if not chain_resp.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Chain not found"
                )

            chain = chain_resp.data[0]

            logger.info(f"[CHAIN LOGIN] Success for: {data.email}, chain: {chain_id}")

            return {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.user_metadata.get("full_name", ""),
                    "user_type": "chain_owner"
                },
                "chain": {
                    "id": chain["id"],
                    "chain_name": chain["chain_name"],
                    "is_active": chain.get("is_active", False),
                    "total_outlets": chain.get("total_outlets", 0),
                    "plan_end_date": chain.get("plan_end_date")
                },
                "access_token": auth_response.session.access_token,
                "refresh_token": auth_response.session.refresh_token,
                "token_type": "bearer"
            }

        except HTTPException:
            raise
        except Exception as e:
            err_msg = str(e).lower()
            if "invalid login credentials" in err_msg or "invalid_credentials" in err_msg:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            logger.error(f"Chain login error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {str(e)}"
            )

    @staticmethod
    async def get_chain_outlets(chain_id: str) -> List[Dict]:
        """Get all single outlets belonging to a chain"""
        try:
            db = get_fresh_supabase_client()
            response = db.table("single_outlets").select(
                "id, outlet_name, outlet_type, owner_name, owner_email, owner_phone, "
                "address, city, state, pincode, is_active, plan_end_date, license_key, "
                "created_at"
            ).eq("chain_id", chain_id).order("created_at").execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching chain outlets: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch outlets: {str(e)}"
            )

    @staticmethod
    async def get_outlet_stats(outlet_id: str, date_str: str) -> Dict:
        """Get detailed stats for a specific outlet on a date"""
        try:
            db = get_fresh_supabase_client()

            # Try to get existing analysis
            analysis_resp = db.table("kds_daily_analysis").select("*").eq(
                "outlet_id", outlet_id
            ).eq("analysis_date", date_str).maybe_single().execute()

            if analysis_resp.data:
                return analysis_resp.data

            # Generate from orders if not found
            start_utc, end_utc = _to_ist_date_range_utc(date_str)

            orders_resp = db.table("kds_orders").select("*").eq(
                "outlet_id", outlet_id
            ).gte("created_at", start_utc).lt("created_at", end_utc).execute()

            orders = orders_resp.data or []

            dine_in_count = takeaway_count = delivery_count = 0
            dine_in_revenue = takeaway_revenue = delivery_revenue = 0.0
            cash_count = card_count = upi_count = razorpay_count = other_count = 0
            cash_revenue = card_revenue = upi_revenue = razorpay_revenue = other_revenue = 0.0
            cancelled_orders = 0
            total_tax = total_discount = 0.0

            for order in orders:
                if (order.get("order_status") or "").lower() == "cancelled":
                    cancelled_orders += 1
                    continue

                amount = float(order.get("total_amount") or 0)
                order_type = (order.get("order_type") or "").lower()

                if order_type in ("dine-in", "dine_in"):
                    dine_in_count += 1
                    dine_in_revenue += amount
                elif order_type in ("takeaway", "pickup"):
                    takeaway_count += 1
                    takeaway_revenue += amount
                elif order_type == "delivery":
                    delivery_count += 1
                    delivery_revenue += amount

                pm = (order.get("payment_method") or "").lower()
                if pm == "cash":
                    cash_count += 1
                    cash_revenue += amount
                elif pm in ("card", "debit card", "credit card"):
                    card_count += 1
                    card_revenue += amount
                elif pm == "upi":
                    upi_count += 1
                    upi_revenue += amount
                elif pm in ("razorpay", "online"):
                    razorpay_count += 1
                    razorpay_revenue += amount
                elif pm:
                    other_count += 1
                    other_revenue += amount

                total_tax += float(order.get("tax_amount") or 0)
                total_discount += float(order.get("discount_amount") or 0)

            total_orders = dine_in_count + takeaway_count + delivery_count
            total_revenue = dine_in_revenue + takeaway_revenue + delivery_revenue
            avg_order = total_revenue / total_orders if total_orders > 0 else 0.0

            return {
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
                "average_order_value": round(avg_order, 2),
                "tax_collected": round(total_tax, 2),
                "discount_given": round(total_discount, 2),
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching outlet stats: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch outlet stats: {str(e)}"
            )

    @staticmethod
    async def get_chain_dashboard(chain_id: str, date_str: str) -> Dict:
        """Aggregate dashboard data across all outlets in a chain"""
        try:
            # Get all outlets
            outlets = await ChainOwnerService.get_chain_outlets(chain_id)

            total_revenue = 0.0
            total_orders = 0
            total_dine_in = total_takeaway = total_delivery = 0
            total_cancelled = 0
            outlet_summaries = []

            for outlet in outlets:
                outlet_id = outlet["id"]
                stats = await ChainOwnerService.get_outlet_stats(outlet_id, date_str)

                rev = float(stats.get("total_revenue", 0))
                ords = int(stats.get("total_orders", 0))

                total_revenue += rev
                total_orders += ords
                total_dine_in += int(stats.get("dine_in_count", 0))
                total_takeaway += int(stats.get("takeaway_count", 0))
                total_delivery += int(stats.get("delivery_count", 0))
                total_cancelled += int(stats.get("cancelled_orders", 0))

                outlet_summaries.append({
                    "outlet_id": outlet_id,
                    "outlet_name": outlet.get("outlet_name", ""),
                    "city": outlet.get("city", ""),
                    "is_active": outlet.get("is_active", False),
                    "total_orders": ords,
                    "total_revenue": round(rev, 2),
                    "dine_in_count": stats.get("dine_in_count", 0),
                    "takeaway_count": stats.get("takeaway_count", 0),
                    "delivery_count": stats.get("delivery_count", 0),
                    "dine_in_revenue": stats.get("dine_in_revenue", 0),
                    "takeaway_revenue": stats.get("takeaway_revenue", 0),
                    "delivery_revenue": stats.get("delivery_revenue", 0),
                })

            avg_order = total_revenue / total_orders if total_orders > 0 else 0.0

            return {
                "date": date_str,
                "total_outlets": len(outlets),
                "active_outlets": sum(1 for o in outlets if o.get("is_active")),
                "total_revenue": round(total_revenue, 2),
                "total_orders": total_orders,
                "average_order_value": round(avg_order, 2),
                "total_dine_in": total_dine_in,
                "total_takeaway": total_takeaway,
                "total_delivery": total_delivery,
                "total_cancelled": total_cancelled,
                "outlets": outlet_summaries,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating chain dashboard: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate dashboard: {str(e)}"
            )
