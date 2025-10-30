import argparse
import json
import os
import sys
from typing import Optional

import requests
from supabase import Client, create_client


def ping_auth_settings(url: str, key: str) -> dict:
    endpoint = url.rstrip("/") + "/auth/v1/settings"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }
    try:
        resp = requests.get(endpoint, headers=headers, timeout=10)
        return {
            "ok": resp.status_code == 200,
            "status": resp.status_code,
            "error": None if resp.ok else resp.text[:300],
        }
    except Exception as e:
        return {"ok": False, "status": None, "error": str(e)}


def test_table_query(client: Client, table: str) -> dict:
    try:
        res = client.table(table).select("*", count="exact").limit(1).execute()
        count = getattr(res, "count", None)
        data_preview = res.data[0] if isinstance(res.data, list) and res.data else None
        return {
            "ok": True,
            "count": count,
            "data_preview": data_preview,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Quick Supabase connectivity check")
    parser.add_argument(
        "--url",
        dest="url",
        default=os.getenv("SUPABASE_URL"),
        help="Supabase project URL (or env SUPABASE_URL)",
    )
    parser.add_argument(
        "--key",
        dest="key",
        default=os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY"),
        help="Supabase anon key (or env SUPABASE_ANON_KEY)",
    )
    parser.add_argument(
        "--table",
        dest="table",
        default=os.getenv("TEST_TABLE_NAME"),
        help="Optional table name to query for PostgREST access",
    )
    args = parser.parse_args()

    if not args.url or not args.key:
        print(
            "Missing SUPABASE_URL or SUPABASE_ANON_KEY. Provide via env or --url/--key.",
            file=sys.stderr,
        )
        sys.exit(2)

    auth_result = ping_auth_settings(args.url, args.key)

    table_result: Optional[dict] = None
    if args.table:
        try:
            client: Client = create_client(args.url, args.key)
            table_result = test_table_query(client, args.table)
        except Exception as e:
            table_result = {"ok": False, "error": str(e)}

    output = {
        "url": args.url,
        "auth_settings": auth_result,
        "table": args.table,
        "table_query": table_result,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
