import { supabase } from "../lib/supabase";

export interface Routine {
    id: string;
    date: string;
    morningProducts: number[];
    eveningProducts: number[];
    skinConditionRating?: number;
    notes?: string;
    createdAt: string;
    updatedAt: string;
}

export interface RoutineInput {
    date: string;
    morningProducts: number[];
    eveningProducts: number[];
    skinConditionRating?: number;
    notes?: string;
}

export interface TrendAnalysis {
    routineCount: number;
    avgRating: number;
    totalProductsUsed: number;
    analysis: string;
}

// Create or update a routine (upsert based on date)
export async function createRoutine(input: RoutineInput): Promise<Routine> {
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
        throw new Error("Not authenticated");
    }

    // Check if routine exists for this date
    const { data: existing } = await supabase
        .from("skincare_routine")
        .select("*")
        .eq("user_id", user.id)
        .eq("date", input.date)
        .single();

    if (existing) {
        // Update existing
        const { data, error } = await supabase
            .from("skincare_routine")
            .update({
                morning_products: input.morningProducts,
                evening_products: input.eveningProducts,
                skin_condition_rating: input.skinConditionRating || null,
                notes: input.notes || null,
            })
            .eq("user_id", user.id)
            .eq("date", input.date)
            .select()
            .single();

        if (error) throw error;
        return mapRoutine(data);
    } else {
        // Insert new
        const { data, error } = await supabase
            .from("skincare_routine")
            .insert({
                user_id: user.id,
                date: input.date,
                morning_products: input.morningProducts,
                evening_products: input.eveningProducts,
                skin_condition_rating: input.skinConditionRating || null,
                notes: input.notes || null,
            })
            .select()
            .single();

        if (error) throw error;
        return mapRoutine(data);
    }
}

// Get all routines for the current user
export async function getUserRoutines(): Promise<Routine[]> {
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
        throw new Error("Not authenticated");
    }

    const { data, error } = await supabase
        .from("skincare_routine")
        .select("*")
        .eq("user_id", user.id)
        .order("date", { ascending: false });

    if (error) throw error;
    return (data || []).map(mapRoutine);
}

// Get trend analysis
export async function getTrendAnalysis(): Promise<TrendAnalysis> {
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
        throw new Error("Not authenticated");
    }

    const { data, error } = await supabase
        .from("skincare_routine")
        .select("*")
        .eq("user_id", user.id)
        .order("date", { ascending: false });

    if (error) throw error;

    if (!data || data.length === 0) {
        return {
            routineCount: 0,
            avgRating: 0,
            totalProductsUsed: 0,
            analysis: "Start logging your skincare routine to see insights and trends. Track your skin condition over time to identify patterns and improvements.",
        };
    }

    // Calculate statistics
    const avgRating = data
        .filter((r) => r.skin_condition_rating)
        .reduce((sum, r) => sum + r.skin_condition_rating, 0) /
        data.filter((r) => r.skin_condition_rating).length;

    const totalProductsUsed = new Set(
        data.flatMap((r) => [
            ...(r.morning_products || []),
            ...(r.evening_products || []),
        ])
    ).size;

    // Generate insights
    let insights = `You've logged ${data.length} routine${data.length !== 1 ? "s" : ""} so far. `;

    if (avgRating) {
        insights += `Your average skin condition rating is ${avgRating.toFixed(1)}/5. `;

        if (avgRating >= 4) {
            insights += "Your skin appears to be responding well to your routine! ";
        } else if (avgRating >= 3) {
            insights += "Consider tracking which products work best for your skin. ";
        } else {
            insights += "You might want to review your product selections and consult with a dermatologist if irritation persists. ";
        }
    }

    if (totalProductsUsed > 0) {
        insights += `You've used ${totalProductsUsed} unique products across your routines. `;
    }

    // Check for recent patterns
    const recentData = data.slice(0, 7);
    const recentRatings = recentData
        .filter((r) => r.skin_condition_rating)
        .map((r) => r.skin_condition_rating);

    if (recentRatings.length >= 3) {
        const trend =
            recentRatings[0] - recentRatings[recentRatings.length - 1];

        if (trend > 0.5) {
            insights += "Your recent skin condition shows improvement! ";
        } else if (trend < -0.5) {
            insights += "Your skin condition has declined recently - consider reviewing what might have changed. ";
        }
    }

    insights += "Keep logging your routine to track long-term patterns and effectiveness.";

    return {
        routineCount: data.length,
        avgRating: avgRating || 0,
        totalProductsUsed,
        analysis: insights,
    };
}

function mapRoutine(row: any): Routine {
    return {
        id: row.id,
        date: row.date,
        morningProducts: row.morning_products || [],
        eveningProducts: row.evening_products || [],
        skinConditionRating: row.skin_condition_rating,
        notes: row.notes,
        createdAt: row.created_at,
        updatedAt: row.updated_at,
    };
}

