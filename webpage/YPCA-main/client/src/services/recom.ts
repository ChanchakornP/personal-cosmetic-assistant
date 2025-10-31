export type SkinProfile = {
    skinType?: string;
    concerns?: string[];
    preferredCategories?: string[];
    budgetRange?: { min?: number; max?: number };
    excludeProducts?: (string | number)[];
};

export async function getRecommendations(params: {
    skinProfile: SkinProfile;
    limit?: number;
    strategy?: "content" | "popularity" | "hybrid";
}) {
    const base = (import.meta.env.VITE_RECOM_API_URL as string) || "http://localhost:8001";
    const res = await fetch(`${base}/api/recommendations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error(`Recommendation failed (${res.status})`);
    return res.json();
}


