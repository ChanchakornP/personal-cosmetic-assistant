import os
from typing import List, Optional, Annotated
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from dotenv import load_dotenv
from supabase import create_client, Client
import requests

# ---------- 环境与客户端 ----------
load_dotenv()
SUPABASE_URL = os.getenv("https://qmjcouwjzjnaqdbcyray.supabase.co")
SUPABASE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFtamNvdXdqempuYXFkYmN5cmF5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2NTgzODEsImV4cCI6MjA3NzIzNDM4MX0.DSAkDRhNit9UmZMXGpylQGTPLkMY8KvDR1VdXVGg2o8")  
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(".env setting SUPABASE_URL and SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Products API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- DTO（API 层使用 camelCase） ----------
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

# ---------- 映射：DB <-> DTO ----------
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
    if dto.name is not None: payload["name"] = dto.name
    if dto.description is not None: payload["description"] = dto.description
    if dto.price is not None: payload["price"] = dto.price
    if dto.stock is not None: payload["stock"] = dto.stock
    if dto.category is not None: payload["category"] = dto.category
    if dto.mainImageUrl is not None: payload["main_image_url"] = dto.mainImageUrl
    return payload

# ---------- CRUD ----------
@app.get("/api/products", response_model=List[ProductDTO])
def list_products(
    q: Annotated[Optional[str], Query(description="对 name 做模糊搜索")] = None,
    category: Annotated[Optional[str], Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    sort: Annotated[str, Query(description="field:asc|desc")] = "created_at:desc",
):
    query = supabase.table("Product").select("*")
    if q:
        query = query.ilike("name", f"%{q}%")
    if category:
        query = query.eq("category", category)

    # 排序
    field, direction = (sort.split(":") + ["asc"])[:2]
    query = query.order(field, desc=(direction.lower() == "desc"))

    # 分页（PostgREST 使用 range）
    query = query.range(offset, offset + limit - 1)

    res = query.execute()
    rows = res.data or []
    return [db_to_dto(r) for r in rows]

@app.get("/api/products/{product_id}", response_model=ProductDTO)
def get_product(product_id: int):
    res = supabase.table("Product").select("*").eq("id", product_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_to_dto(res.data)

@app.post("/api/products", response_model=ProductDTO, status_code=201)
def create_product(payload: ProductCreateDTO):
    db_row = dto_to_db_create(payload)
    res = supabase.table("Product").insert(db_row).select("*").single().execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Failed to create product")
    return db_to_dto(res.data)

@app.put("/api/products/{product_id}", response_model=ProductDTO)
def update_product(product_id: int, payload: ProductUpdateDTO):
    db_row = dto_to_db_update(payload)
    if not db_row:
        raise HTTPException(status_code=400, detail="No fields to update")

    res = (
        supabase.table("Product")
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
    exists = supabase.table("Product").select("id").eq("id", product_id).maybe_single().execute()
    if not exists.data:
        raise HTTPException(status_code=404, detail="Product not found")
    supabase.table("Product").delete().eq("id", product_id).execute()
    return None

# ---------- 健康检查 ----------
@app.get("/api/health")
def health():
    res = supabase.table("Product").select("id", count="exact").execute()
    return {"ok": True, "productCount": res.count or 0}

# ---------- 爬虫：抓取 mock 数据并入库 ----------
class CrawlRequest(BaseModel):
    source: Optional[str] = Field(
        default="https://fakestoreapi.com/products", description="返回商品数组的 HTTP 接口"
    )
    limit: Optional[int] = Field(default=12, ge=1, le=200)
    upsert_by_name: bool = True

def _normalize_item(item: dict) -> dict:
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

@app.post("/api/products/crawl", response_model=List[ProductDTO])
def crawl_and_store(req: CrawlRequest = Body(default=CrawlRequest())):
    try:
        resp = requests.get(req.source, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            data = data.get("products") or data.get("items") or []
        if not isinstance(data, list):
            raise ValueError("Unexpected response format from source")

        items = data[: req.limit]
        normalized = [_normalize_item(it) for it in items]

        result = []
        for row in normalized:
            if req.upsert_by_name:
                existing = supabase.table("Product").select("id").eq("name", row["name"]).maybe_single().execute()
                if existing.data and isinstance(existing.data, dict) and existing.data.get("id"):
                    res = (
                        supabase.table("Product")
                        .update(row)
                        .eq("id", existing.data["id"])
                        .select("*")
                        .single()
                        .execute()
                    )
                else:
                    res = supabase.table("Product").insert(row).select("*").single().execute()
            else:
                res = supabase.table("Product").insert(row).select("*").single().execute()

            if res.data:
                result.append(db_to_dto(res.data))

        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Crawl failed: {e}")

