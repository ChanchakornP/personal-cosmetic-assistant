import { supabase } from "../lib/supabase";
import type { FacialAnalysisResponse } from "./recom";

export type FacialAnalysisHistory = {
    id: string;
    userId: string;
    skinType: string | null;
    detectedConcerns: string[];
    analysisResult: string;
    productIds: number[];
    recommendationReasons: Record<string, string | string[]> | null;
    inputSkinType: string | null;
    inputConcerns: string[] | null;
    budgetRange: { min?: number; max?: number } | null;
    createdAt: string;
    updatedAt: string;
};

export type SaveHistoryData = {
    skinType: string;
    detectedConcerns: string[];
    analysisResult: string;
    productIds: number[];
    recommendationReasons?: Record<string, string | string[]>;
    inputSkinType?: string;
    inputConcerns?: string[];
    budgetRange?: { min?: number; max?: number };
};

/**
 * Save facial analysis history to Supabase
 */
export async function saveFacialAnalysisHistory(
    data: SaveHistoryData
): Promise<FacialAnalysisHistory> {
    const {
        data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
        throw new Error("User must be authenticated to save history");
    }

    const { data: history, error } = await supabase
        .from("facial_analysis_history")
        .insert({
            user_id: user.id,
            skin_type: data.skinType,
            detected_concerns: data.detectedConcerns,
            analysis_result: data.analysisResult,
            product_ids: data.productIds,
            recommendation_reasons: data.recommendationReasons || null,
            input_skin_type: data.inputSkinType || null,
            input_concerns: data.inputConcerns || null,
            budget_range: data.budgetRange || null,
        })
        .select()
        .single();

    if (error) {
        throw new Error(`Failed to save history: ${error.message}`);
    }

    return mapDbRowToHistory(history);
}

/**
 * Fetch user's facial analysis history (most recent first)
 */
export async function getFacialAnalysisHistory(): Promise<
    FacialAnalysisHistory[]
> {
    const {
        data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
        throw new Error("User must be authenticated to fetch history");
    }

    const { data, error } = await supabase
        .from("facial_analysis_history")
        .select("*")
        .eq("user_id", user.id)
        .order("created_at", { ascending: false });

    if (error) {
        throw new Error(`Failed to fetch history: ${error.message}`);
    }

    return (data || []).map(mapDbRowToHistory);
}

/**
 * Delete a specific history entry
 */
export async function deleteFacialAnalysisHistory(
    id: string
): Promise<void> {
    const {
        data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
        throw new Error("User must be authenticated to delete history");
    }

    const { error } = await supabase
        .from("facial_analysis_history")
        .delete()
        .eq("id", id)
        .eq("user_id", user.id); // Extra safety check

    if (error) {
        throw new Error(`Failed to delete history: ${error.message}`);
    }
}

/**
 * Map database row to History type
 */
function mapDbRowToHistory(row: any): FacialAnalysisHistory {
    return {
        id: row.id,
        userId: row.user_id,
        skinType: row.skin_type,
        detectedConcerns: row.detected_concerns || [],
        analysisResult: row.analysis_result,
        productIds: row.product_ids || [],
        recommendationReasons: row.recommendation_reasons || null,
        inputSkinType: row.input_skin_type,
        inputConcerns: row.input_concerns || [],
        budgetRange: row.budget_range,
        createdAt: row.created_at,
        updatedAt: row.updated_at,
    };
}

/**
 * Extract product IDs and recommendation reasons from analysis response
 */
export function extractHistoryData(
    response: FacialAnalysisResponse,
    inputData?: {
        skinType?: string;
        concerns?: string[];
        budgetRange?: { min?: number; max?: number };
    }
): SaveHistoryData {
    const productIds =
        response.recommendations?.products?.map((p) => Number(p.id)) || [];

    // Normalize reasons - convert Record<string, string> to Record<string, string | string[]>
    let recommendationReasons: Record<string, string | string[]> | undefined;
    if (response.recommendations?.reasons) {
        recommendationReasons = {};
        for (const [key, value] of Object.entries(response.recommendations.reasons)) {
            // If value is already an array, use it; otherwise convert string to array
            recommendationReasons[key] = Array.isArray(value) ? value : [value];
        }
    }

    return {
        skinType: response.skinType,
        detectedConcerns: response.detectedConcerns,
        analysisResult: response.analysisResult,
        productIds,
        recommendationReasons,
        inputSkinType: inputData?.skinType,
        inputConcerns: inputData?.concerns,
        budgetRange: inputData?.budgetRange,
    };
}

