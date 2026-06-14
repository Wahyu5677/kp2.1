import sys
from pathlib import Path

from werkzeug.security import generate_password_hash

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import Config
from supabase_rest import SupabaseRESTClient


def is_hashed(value: str) -> bool:
    if not value:
        return False
    return value.startswith("pbkdf2:") or value.startswith("scrypt:")


def main():
    Config.validate()
    supabase = SupabaseRESTClient(
        url=Config.SUPABASE_URL,
        service_role_key=Config.SUPABASE_SERVICE_ROLE_KEY,
    )

    users = supabase.select(table="users", columns="id_user,username,password")

    updated = 0
    for user in users:
        raw = user.get("password") or ""
        if is_hashed(raw):
            continue

        hashed = generate_password_hash(raw)
        supabase.update(
            table="users",
            filters={"id_user": f"eq.{user['id_user']}"},
            payload={"password": hashed},
        )
        updated += 1
        print(f"[OK] user '{user.get('username')}' di-hash")

    print(f"Selesai. Total user diupdate: {updated}")


if __name__ == "__main__":
    main()
