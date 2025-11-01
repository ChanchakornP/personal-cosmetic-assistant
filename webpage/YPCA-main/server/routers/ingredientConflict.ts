import { z } from "zod";
import { router, publicProcedure } from "../trpc";
import { supabaseAdmin } from "../lib/supabase-server";

const RECOM_API_URL = process.env.RECOM_API_URL || "http://localhost:8001";

export const ingredientConflictRouter = router({
    analyze: publicProcedure
        .input(
            z.object({
                productIds: z.array(z.number()).min(2, "Please select at least 2 products"),
            })
        )
        .mutation(async ({ input }) => {
            try {
                // First, fetch products from Supabase to get ingredient information
                const { data: products, error: productsError } = await supabaseAdmin
                    .from("product")
                    .select("id, name, ingredients")
                    .in("id", input.productIds);

                if (productsError) {
                    throw new Error(`Failed to fetch products: ${productsError.message}`);
                }

                if (!products || products.length < 2) {
                    throw new Error("Could not find the selected products");
                }

                // Prepare products for LLM analysis
                const productsForAnalysis = products.map((p) => ({
                    id: p.id,
                    name: p.name,
                    ingredients: p.ingredients || "Not specified",
                }));

                // Call recomsystem API for LLM-based conflict analysis
                const response = await fetch(`${RECOM_API_URL}/api/ingredient-conflict`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        products: productsForAnalysis,
                    }),
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`Conflict analysis failed: ${response.status} - ${errorText}`);
                }

                const result = await response.json();

                return {
                    conflictDetected: result.conflictDetected || false,
                    conflictDetails: result.conflictDetails || "Analysis completed.",
                    safetyWarning: result.safetyWarning || undefined,
                    alternatives: result.alternatives || [],
                };
            } catch (error) {
                console.error("[ingredientConflict.analyze] Error:", error);
                throw error;
            }
        }),

    getUserConflicts: publicProcedure.query(async () => {
        // Return empty array - we're not storing conflict history
        // This is kept for API compatibility but doesn't persist data
        return [];
    }),
});

