import os
import glob
from typing import List, Optional, Dict, Any, Annotated

import requests
import pandas as pd
from kaggle.api.kaggle_api_extended import KaggleApi
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from supabase import create_client, Client


# -------------------- Environment and Supabase Client --------------------
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Setting SUPABASE_URL and SUPABASE_ANON_KEY in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Products API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Front-end domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------- DTO（API layer using camelCase） --------------------
class ProductDTO(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    category: Optional[str] = None
    mainImageUrl: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductCreateDTO(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    price: float
    stock: int = 0
    category: Optional[str] = None
    mainImageUrl: Optional[str] = None


class ProductUpdateDTO(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    mainImageUrl: Optional[str] = None


# -------------------- DB <-> DTO --------------------
def db_to_dto(row: dict) -> ProductDTO:
    return ProductDTO(
        id=row["id"],
        name=row["name"],
        description=row.get("description"),
        price=float(row["price"]),
        stock=row.get("stock", 0),
        category=row.get("category"),
        mainImageUrl=row.get("main_image_url"),
        createdAt=row.get("created_at"),
        updatedAt=row.get("updated_at"),
    )


def dto_to_db_create(dto: ProductCreateDTO) -> dict:
    return {
        "name": dto.name,
        "description": dto.description,
        "price": dto.price,
        "stock": dto.stock,
        "category": dto.category,
        "main_image_url": dto.mainImageUrl,
    }


def dto_to_db_update(dto: ProductUpdateDTO) -> dict:
    payload = {}
    if dto.name is not None:
        payload["name"] = dto.name
    if dto.description is not None:
        payload["description"] = dto.description
    if dto.price is not None:
        payload["price"] = dto.price
    if dto.stock is not None:
        payload["stock"] = dto.stock
    if dto.category is not None:
        payload["category"] = dto.category
    if dto.mainImageUrl is not None:
        payload["main_image_url"] = dto.mainImageUrl
    return payload


# -------------------- CRUD --------------------
@app.get("/api/products", response_model=List[ProductDTO])
def list_products(
    q: Annotated[Optional[str], Query(description="Perform a fuzzy search on name")] = None,
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
    try:
        res = supabase.table("product").insert(db_row).select("*").single().execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create product: {e}")
    if not res.data:
        raise HTTPException(status_code=400, detail="Failed to create product")
    return db_to_dto(res.data)


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
    return db_to_dto(res.data)


@app.delete("/api/products/{product_id}", status_code=204)
def delete_product(product_id: int):
    exists = supabase.table("product").select("id").eq("id", product_id).maybe_single().execute()
    if not exists.data:
        raise HTTPException(status_code=404, detail="Product not found")
    supabase.table("product").delete().eq("id", product_id).execute()
    return None


@app.get("/api/health")
def health():
    res = supabase.table("product").select("id", count="exact").execute()
    return {"ok": True, "productCount": res.count or 0}


# -------------------- Web crawling / Importing data from Kaggle --------------------
class CrawlRequest(BaseModel):
    # If it's not Kaggle import, then get fake data from fakeapi
    source: Optional[str] = Field(
        default="https://fakestoreapi.com/products",
        description="HTTP interface that returns an array of goods; Or use kaggle:cosmetics-ingredients",
    )
    limit: Optional[int] = Field(default=12, ge=1, le=200)
    upsert_by_name: bool = True  # Duplicate names are removed using the name attribute (name = Brand - Name)


def _normalize_item(item: dict) -> dict:
    """JSON mock (e.g., fakestore) generic mapping"""
    name = str(item.get("title") or item.get("name") or "Untitled").strip()
    description = str(item.get("description") or "")[:5000]
    price = float(item.get("price") or 0.0)
    category = str(item.get("category") or "") or None
    image = item.get("image") or (
        item.get("images")[0] if isinstance(item.get("images"), list) and item.get("images") else None
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
    Reading kingabzpro/cosmetics-datasets
      - name = Brand - Name
      - description = Ingredients
      - category = Label
      - price = Price
      - stock = 0
      - main_image_url = None
    """
    target_dir = os.path.join(os.getcwd(), "data_kaggle_cosmetics")
    os.makedirs(target_dir, exist_ok=True)

    if not any(glob.glob(os.path.join(target_dir, "*"))):
        api = KaggleApi()
        api.authenticate()
        api.dataset_download_files("kingabzpro/cosmetics-datasets", path=target_dir, unzip=True)

    csv_files = [p for p in glob.glob(os.path.join(target_dir, "*.csv"))]
    if not csv_files:
        raise ValueError("Did not find the CSV file, please try again!")

    wanted_cols = {"name", "brand", "ingredients", "label", "price"}
    results: List[Dict[str, Any]] = []

    def norm_cols(cols):
        return {c: c.lower().strip() for c in cols}

    for csv_path in csv_files:
        try:
            df = pd.read_csv(csv_path)
        except Exception:
            continue

        col_map = norm_cols(df.columns)
        inv_map = {v: k for k, v in col_map.items()}

        present = wanted_cols.intersection(set(col_map.values()))
        if len(present) < 3:
            continue

        c_name = inv_map.get("name") or inv_map.get("product") or inv_map.get("product_name")
        c_brand = inv_map.get("brand") or inv_map.get("brand_name")
        c_ing = inv_map.get("ingredients") or inv_map.get("ingredient_list")
        c_label = inv_map.get("label") or inv_map.get("category") or inv_map.get("type")
        c_price = inv_map.get("price") or inv_map.get("list_price") or inv_map.get("price_usd")

        # Need Name / Ingredients / Price
        if not (c_name and c_ing and c_price):
            continue

        for _, row in df.head(limit).iterrows():
            name_v = str(row.get(c_name) if c_name in df.columns else "").strip()
            brand_v = str(row.get(c_brand) if c_brand in df.columns else "").strip() if c_brand else ""
            ing_v = str(row.get(c_ing) if c_ing in df.columns else "").strip()
            label_v = str(row.get(c_label) if c_label in df.columns else "").strip() if c_label else None

            try:
                price_v = float(row.get(c_price)) if c_price and pd.notna(row.get(c_price)) else 0.0
            except Exception:
                price_v = 0.0

            merged_name = f"{brand_v} - {name_v}" if (brand_v and name_v) else (brand_v or name_v or "Untitled")

            results.append(
                {
                    "name": merged_name,
                    "description": ing_v or "",  # Ingredients
                    "price": price_v,            # Price
                    "stock": 0,
                    "category": label_v,         # Label
                    "main_image_url": None,
                }
            )

        if results:
            break

    if not results:
        raise ValueError("Did not find any Name/Brand/Ingredients/Label/Price columns.")

    return results


@app.post("/api/products/crawl", response_model=List[ProductDTO])
def crawl_and_store(req: CrawlRequest = Body(default=CrawlRequest())):
    try:
        # If the source is specified as a Kaggle feature string, proceed with the Kaggle import logic
        if str(req.source).startswith("kaggle:cosmetics-ingredients"):
            normalized = fetch_from_kaggle_cosmetics(req.limit or 100)
        else:
            # The default is to use fakestore
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
            if req.upsert_by_name:
                existing = (
                    supabase.table("product")
                    .select("id")
                    .eq("name", row["name"])
                    .maybe_single()
                    .execute()
                )
                if existing.data and isinstance(existing.data, dict) and existing.data.get("id"):
                    res = (
                        supabase.table("product")
                        .update(row)
                        .eq("id", existing.data["id"])
                        .select("*")
                        .single()
                        .execute()
                    )
                else:
                    res = supabase.table("product").insert(row).select("*").single().execute()
            else:
                res = supabase.table("product").insert(row).select("*").single().execute()

            if res.data:
                result.append(db_to_dto(res.data))

        return result

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Crawl failed: {e}")
