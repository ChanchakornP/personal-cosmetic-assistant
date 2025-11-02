import { supabase } from "../lib/supabase";
import type { Product } from "../types/product";

type ProductRow = {
    id: string;
    name: string;
    brand?: string | null;
    description?: string | null;
    price?: number | null; // dollars
    category?: string | null;
    rank?: number | null;
    main_image_url?: string | null;
    stock?: number | null;
    created_at?: string | null;
    updated_at?: string | null;
};

export async function fetchProducts(): Promise<Product[]> {
    const { data, error } = await supabase
        .from("product")
        .select("id, name, brand, description, price, category, rank, main_image_url, stock, ingredients")
        .order("name");

    if (error) throw error;

    const rows = (data as ProductRow[]) ?? [];
    return rows.map((p) => ({
        id: String(p.id),
        name: p.name,
        brand: p.brand ?? undefined,
        category: p.category ?? undefined,
        priceCents: Math.round(((p.price ?? 0) as number) * 100),
        imageUrl: p.main_image_url ?? undefined,
        description: p.description ?? undefined,
        stock: p.stock ?? undefined,
        ingredients: (p as any).ingredients ?? undefined,
    }));
}


