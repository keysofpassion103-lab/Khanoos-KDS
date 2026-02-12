"""
Debug script to check admin login issues
"""
import asyncio
from app.database import supabase
from app.auth.utils import get_password_hash, verify_password

async def check_admin_users():
    """Check all admin users in database"""
    print("=" * 60)
    print("CHECKING ADMIN USERS IN DATABASE")
    print("=" * 60)

    try:
        # Fetch all admin users
        response = supabase.table("admin_users").select("*").execute()

        if not response.data:
            print("\n❌ NO ADMIN USERS FOUND IN DATABASE!")
            print("\nTo create an admin user, use the /register endpoint:")
            print("POST /api/v1/admin-auth/register")
            print("""
{
  "email": "admin@example.com",
  "password": "Admin@123",
  "full_name": "Admin User",
  "phone": "+1234567890"
}
            """)
            return

        print(f"\n✅ Found {len(response.data)} admin user(s):")
        print("-" * 60)

        for idx, admin in enumerate(response.data, 1):
            print(f"\nAdmin #{idx}:")
            print(f"  ID: {admin['id']}")
            print(f"  Email: {admin['email']}")
            print(f"  Full Name: {admin['full_name']}")
            print(f"  Phone: {admin.get('phone', 'N/A')}")
            print(f"  Created: {admin['created_at']}")
            print(f"  Password Hash: {admin['password_hash'][:50]}...")

            # Test password verification with common passwords
            test_passwords = ["Admin@123", "admin123", "password", "12345678"]
            print(f"\n  Testing common passwords:")
            for pwd in test_passwords:
                is_valid = verify_password(pwd, admin['password_hash'])
                status = "✅ MATCH" if is_valid else "❌ No match"
                print(f"    - '{pwd}': {status}")

        print("\n" + "=" * 60)
        print("RECOMMENDATIONS:")
        print("=" * 60)
        print("\n1. If no password matches, create a new admin user via /register endpoint")
        print("2. Use the exact email and password you created")
        print("3. Make sure there are no extra spaces in email/password")
        print("4. Password requirements: min 8 chars, at least 1 digit, 1 uppercase")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nMake sure:")
        print("1. Supabase credentials in .env are correct")
        print("2. admin_users table exists in Supabase")
        print("3. You have network connection to Supabase")

async def create_test_admin():
    """Create a test admin user"""
    print("\n" + "=" * 60)
    print("CREATING TEST ADMIN USER")
    print("=" * 60)

    test_email = "admin@test.com"
    test_password = "Admin@123"

    try:
        # Check if admin already exists
        existing = supabase.table("admin_users").select("id").eq("email", test_email).execute()

        if existing.data:
            print(f"\n⚠️  Admin with email '{test_email}' already exists!")
            print("   Use this to login or delete it from Supabase first.")
            return

        # Create new admin
        hashed_password = get_password_hash(test_password)

        insert_data = {
            "email": test_email,
            "password_hash": hashed_password,
            "full_name": "Test Admin",
            "phone": "+1234567890"
        }

        response = supabase.table("admin_users").insert(insert_data).execute()

        if response.data:
            print(f"\n✅ Test admin created successfully!")
            print(f"\nLogin credentials:")
            print(f"  Email: {test_email}")
            print(f"  Password: {test_password}")
            print(f"\nUse these to test login at POST /api/v1/admin-auth/login")
        else:
            print(f"\n❌ Failed to create test admin")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

async def main():
    print("\n🔍 ADMIN LOGIN DIAGNOSTIC TOOL\n")

    # First check existing admins
    await check_admin_users()

    # Ask if user wants to create test admin
    print("\n" + "=" * 60)
    create_test = input("\nDo you want to create a test admin user? (y/n): ").strip().lower()

    if create_test == 'y':
        await create_test_admin()

    print("\n✅ Diagnostic complete!\n")

if __name__ == "__main__":
    asyncio.run(main())
