import { router, publicProcedure } from "../trpc";
import { supabaseAdmin } from "../lib/supabase-server";

export const productRouter = router({
    list: publicProcedure.query(async () => {
        try {
            const { data, error } = await supabaseAdmin
                .from("product")
                .select("id, name, brand, description, price, category, main_image_url, stock, ingredients")
                .order("name");

            if (error) {
                throw new Error(error.message);
            }

            return (data || []).map((p) => ({
                id: Number(p.id),
                name: p.name,
                brand: p.brand || undefined,
                description: p.description || undefined,
                category: p.category || undefined,
                price: p.price || 0,
                imageUrl: p.main_image_url || undefined,
                stock: p.stock || 0,
                ingredients: p.ingredients || undefined,
            }));
        } catch (error) {
            console.error("[product.list] Error:", error);
            throw error;
        }
    }),
});

