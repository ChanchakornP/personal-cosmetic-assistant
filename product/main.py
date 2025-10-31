import glob
import os
from typing import Annotated, Any, Dict, List, Optional

import pandas as pd
import requests
from dotenv import load_dotenv
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from kaggle.api.kaggle_api_extended import KaggleApi
from pydantic import BaseModel, ConfigDict, Field
from supabase import Client, create_client

# -------------------- Environment and Supabase Client --------------------
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Setting SUPABASE_URL and SUPABASE_ANON_KEY in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Products API", version="1.0.0")

# -------------------- CORS --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------- DTO（API layer using camelCase） --------------------
class ProductDTO(BaseModel):
    id: int
    name: str
    brand: Optional[str] = None
    description: Optional[str] = None
    price: float
    stock: int
    category: Optional[str] = None
    rank: Optional[float] = None
    ingredients: Optional[str] = None
    combination: Optional[bool] = None
    dry: Optional[bool] = None
    normal: Optional[bool] = None
    oily: Optional[bool] = None
    sensitive: Optional[bool] = None
    mainImageUrl: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductCreateDTO(BaseModel):
    name: str = Field(..., max_length=255)
    brand: Optional[str] = None
    description: Optional[str] = None
    price: float
    stock: int = 0
    category: Optional[str] = None
    rank: Optional[float] = None
    ingredients: Optional[str] = None
    combination: Optional[bool] = False
    dry: Optional[bool] = False
    normal: Optional[bool] = False
    oily: Optional[bool] = False
    sensitive: Optional[bool] = False
    mainImageUrl: Optional[str] = None


class ProductUpdateDTO(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    brand: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    rank: Optional[float] = None
    ingredients: Optional[str] = None
    combination: Optional[bool] = None
    dry: Optional[bool] = None
    normal: Optional[bool] = None
    oily: Optional[bool] = None
    sensitive: Optional[bool] = None
    mainImageUrl: Optional[str] = None


# ---------- 映射：DB <-> DTO ----------
# ---------- 映射：DB <-> DTO ----------
def db_to_dto(row: dict) -> ProductDTO:
    return ProductDTO(
        id=row["id"],
        name=row["name"],
        brand=row.get("brand"),
        description=row.get("description"),
        price=float(row["price"]),
        stock=row.get("stock", 0),
        category=row.get("category"),
        rank=row.get("rank"),
        ingredients=row.get("ingredients"),
        combination=row.get("combination"),
        dry=row.get("dry"),
        normal=row.get("normal"),
        oily=row.get("oily"),
        sensitive=row.get("sensitive"),
        mainImageUrl=row.get("main_image_url"),
        createdAt=row.get("created_at"),
        updatedAt=row.get("updated_at"),
    )


def dto_to_db_create(dto: ProductCreateDTO) -> dict:
    return {
        "name": dto.name,
        "brand": dto.brand,
        "description": dto.description,
        "price": dto.price,
        "stock": dto.stock,
        "category": dto.category,
        "rank": dto.rank,
        "ingredients": dto.ingredients,
        "combination": dto.combination,
        "dry": dto.dry,
        "normal": dto.normal,
        "oily": dto.oily,
        "sensitive": dto.sensitive,
        "main_image_url": dto.mainImageUrl,
    }


def dto_to_db_update(dto: ProductUpdateDTO) -> dict:
    payload: Dict[str, Any] = {}
    for field, value in dto.dict(exclude_none=True).items():
        if field == "mainImageUrl":
            payload["main_image_url"] = value
        else:
            payload[field] = value
    return payload


# ---------- CRUD ----------
# ---------- CRUD ----------
@app.get("/api/products", response_model=List[ProductDTO])
def list_products(
    q: Annotated[
        Optional[str], Query(description="Perform a fuzzy search on name")
    ] = None,
    category: Annotated[Optional[str], Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    sort: Annotated[str, Query(description="field:asc|desc")] = "created_at:desc",
):
    query = supabase.table("product").select("*")
    if q:
        query = query.ilike("name", f"%{q}%")
    if category:
        query = query.eq("category", category)

    field, direction = (sort.split(":") + ["asc"])[:2]
    query = query.order(field, desc=(direction.lower() == "desc"))
    query = query.range(offset, offset + limit - 1)

    res = query.execute()
    rows = res.data or []
    return [db_to_dto(r) for r in rows]


@app.get("/api/products/{product_id}", response_model=ProductDTO)
def get_product(product_id: int):
    res = supabase.table("product").select("*").eq("id", product_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_to_dto(res.data)


@app.post("/api/products", response_model=ProductDTO, status_code=201)
def create_product(payload: ProductCreateDTO):
    db_row = dto_to_db_create(payload)
    res = supabase.table("product").insert(db_row).select("*").single().execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Failed to create product")
    created = res.data[0]
    return db_to_dto(created)


@app.put("/api/products/{product_id}", response_model=ProductDTO)
def update_product(product_id: int, payload: ProductUpdateDTO):
    db_row = dto_to_db_update(payload)
    if not db_row:
        raise HTTPException(status_code=400, detail="No fields to update")

    res = (
        supabase.table("product")
        .update(db_row)
        .eq("id", product_id)
        .select("*")
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Product not found or not updated")
    updated = res.data[0]
    return db_to_dto(updated)


@app.delete("/api/products/{product_id}", status_code=204)
def delete_product(product_id: int):
    exists = (
        supabase.table("product")
        .select("id")
        .eq("id", product_id)
        .maybe_single()
        .execute()
    )
    if not exists.data:
        raise HTTPException(status_code=404, detail="Product not found")
    supabase.table("product").delete().eq("id", product_id).execute()
    return None


# ---------- 健康检查 ----------
# ---------- 健康检查 ----------
@app.get("/api/health")
def health():
    res = supabase.table("product").select("id", count="exact").execute()
    return {"ok": True, "productCount": res.count or 0}


# ---------- 爬虫：抓取 mock 数据并入库 ----------


# -------------------- Web crawling / Importing data from Kaggle --------------------
class CrawlRequest(BaseModel):
    # If it's not Kaggle import, then get fake data from fakeapi
    source: Optional[str] = Field(
        default="https://fakestoreapi.com/products",
        description="HTTP interface that returns an array of goods; Or use kaggle:cosmetics-ingredients",
    )
    limit: Optional[int] = Field(default=12, ge=1, le=200)
    upsert_by_name: bool = True  # Use unique name (Brand - Name) to upsert


def _normalize_item(item: dict) -> dict:
    """JSON mock (e.g., fakestore) generic mapping"""
    name = str(item.get("title") or item.get("name") or "Untitled").strip()
    description = str(item.get("description") or "")[:5000]
    price = float(item.get("price") or 0.0)
    category = str(item.get("category") or "") or None
    image = item.get("image") or (
        item.get("images")[0]
        if isinstance(item.get("images"), list) and item.get("images")
        else None
    )
    stock = int(item.get("stock") or 0)
    return {
        "name": name,
        "description": description,
        "price": price,
        "stock": stock,
        "category": category,
        "main_image_url": image,
    }


def fetch_from_kaggle_cosmetics(limit: int) -> List[Dict[str, Any]]:
    """
    Read kingabzpro/cosmetics-datasets
      - name = Brand - Name
      - brand = Brand
      - description = Ingredients
      - category = Label
      - price = Price
      - rank = Rank
      - skin suitability booleans = Combination/Dry/Normal/Oily/Sensitive
      - stock = 0
      - main_image_url = None
    """
    target_dir = os.path.join(os.getcwd(), "data_kaggle_cosmetics")
    os.makedirs(target_dir, exist_ok=True)

    if not any(glob.glob(os.path.join(target_dir, "*"))):
        api = KaggleApi()
        api.authenticate()
        api.dataset_download_files(
            "kingabzpro/cosmetics-datasets", path=target_dir, unzip=True
        )
        api.dataset_download_files(
            "kingabzpro/cosmetics-datasets", path=target_dir, unzip=True
        )

    csv_files = [p for p in glob.glob(os.path.join(target_dir, "*.csv"))]
    if not csv_files:
        raise ValueError("Did not find the CSV file, please try again!")

    wanted_cols = {
        "name",
        "brand",
        "ingredients",
        "label",
        "price",
        "rank",
        "combination",
        "dry",
        "normal",
        "oily",
        "sensitive",
    }
    results: List[Dict[str, Any]] = []

    def norm_cols(cols):
        return {c: c.lower().strip() for c in cols}

    for csv_path in csv_files:
        try:
            df = pd.read_csv(csv_path)
        except Exception:
            continue

        col_map = norm_cols(df.columns)  # original -> lower
        inv_map = {v: k for k, v in col_map.items()}  # lower -> original

        present = wanted_cols.intersection(set(col_map.values()))
        if len(present.intersection({"name", "ingredients", "price"})) < 3:
            # Require at least the basics
            continue

        # Column aliases from the file
        c_name = (
            inv_map.get("name") or inv_map.get("product") or inv_map.get("product_name")
        )
        c_brand = inv_map.get("brand") or inv_map.get("brand_name")
        c_ing = inv_map.get("ingredients") or inv_map.get("ingredient_list")
        c_label = inv_map.get("label") or inv_map.get("category") or inv_map.get("type")
        c_price = (
            inv_map.get("price")
            or inv_map.get("list_price")
            or inv_map.get("price_usd")
        )
        c_rank = inv_map.get("rank")

        c_comb = inv_map.get("combination")
        c_dry = inv_map.get("dry")
        c_normal = inv_map.get("normal")
        c_oily = inv_map.get("oily")
        c_sensitive = inv_map.get("sensitive")

        if not (c_name and c_ing and c_price):
            continue

        for _, row in df.head(limit).iterrows():
            name_v = str(row.get(c_name) if c_name in df.columns else "").strip()
            brand_v = (
                str(row.get(c_brand) if c_brand in df.columns else "").strip()
                if c_brand
                else ""
            )
            brand_v = (
                str(row.get(c_brand) if c_brand in df.columns else "").strip()
                if c_brand
                else ""
            )
            ing_v = str(row.get(c_ing) if c_ing in df.columns else "").strip()
            label_v = (
                str(row.get(c_label) if c_label in df.columns else "").strip()
                if c_label
                else None
            )

            # price
            try:
                price_raw = (
                    row.get(c_price) if c_price and c_price in df.columns else 0.0
                )
                price_v = float(price_raw) if pd.notna(price_raw) else 0.0
            except Exception:
                price_v = 0.0

            # rank
            try:
                rank_raw = row.get(c_rank) if c_rank and c_rank in df.columns else None
                rank_v = (
                    float(rank_raw)
                    if (rank_raw is not None and pd.notna(rank_raw))
                    else None
                )
            except Exception:
                rank_v = None

            # booleans: anything truthy (1/True/yes) -> True
            def as_bool(col_name: Optional[str]) -> Optional[bool]:
                if not col_name or col_name not in df.columns:
                    return None
                val = row.get(col_name)
                if pd.isna(val):
                    return None
                try:
                    if isinstance(val, str):
                        return val.strip().lower() in {"1", "true", "yes", "y", "t"}
                    return bool(int(val)) if str(val).isdigit() else bool(val)
                except Exception:
                    return bool(val)

            merged_name = (
                f"{brand_v} - {name_v}"
                if (brand_v and name_v)
                else (brand_v or name_v or "Untitled")
            )

            results.append(
                {
                    "name": merged_name,
                    "brand": brand_v or None,
                    "ingredients": ing_v or "",
                    "price": price_v,
                    "stock": 0,
                    "category": label_v,
                    "rank": rank_v,
                    "combination": as_bool(c_comb),
                    "dry": as_bool(c_dry),
                    "normal": as_bool(c_normal),
                    "oily": as_bool(c_oily),
                    "sensitive": as_bool(c_sensitive),
                    "main_image_url": None,
                }
            )

        if results:
            break

    if not results:
        raise ValueError("Did not find required Name/Ingredients/Price columns.")

    return results


@app.post("/api/products/crawl", response_model=List[ProductDTO])
def crawl_and_store(req: CrawlRequest = Body(default=CrawlRequest())):
    """
    Crawl products either from fakestore (default) or from Kaggle cosmetics dataset
    via source="kaggle:cosmetics-ingredients".
    Upserts by name when upsert_by_name=True.
    """
    try:
        # Kaggle import
        if str(req.source).startswith("kaggle:cosmetics-ingredients"):
            normalized = fetch_from_kaggle_cosmetics(req.limit or 100)
        else:
            # Generic HTTP JSON (default: fakestore)
            resp = requests.get(req.source, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                data = data.get("products") or data.get("items") or []
            if not isinstance(data, list):
                raise ValueError("Unexpected response format from source")
            items = data[: req.limit]
            normalized = [_normalize_item(it) for it in items]

        result: List[ProductDTO] = []
        for row in normalized:
            existing = (
                supabase.table("product")
                .select("id")
                .eq("name", row["name"])
                .maybe_single()
                .execute()
            )

            existing_id = None
            if existing and existing.data and isinstance(existing.data, dict):
                existing_id = existing.data.get("id")

            # If exists -> UPDATE
            if existing_id:
                update_res = (
                    supabase.table("product")
                    .update(row)
                    .eq("id", existing_id)
                    .execute()
                )

                # Fetch updated record
                res = (
                    supabase.table("product")
                    .select("*")
                    .eq("id", existing_id)
                    .single()
                    .execute()
                )

            # Else -> INSERT
            else:
                insert_res = supabase.table("product").insert(row).execute()

                # Fetch newly created row
                name = row["name"]
                res = (
                    supabase.table("product")
                    .select("*")
                    .eq("name", name)
                    .single()
                    .execute()
                )

            if not res or not res.data:
                raise HTTPException(
                    status_code=500, detail=f"DB write failed for: {row['name']}"
                )

            result.append(db_to_dto(res.data))

        return result

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Crawl failed: {e}")
