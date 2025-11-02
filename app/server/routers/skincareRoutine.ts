import { z } from "zod";
import { router, protectedProcedure } from "../trpc";
import { TRPCError } from "@trpc/server";

// Input validation schemas
const skinConditionSchema = z.object({
    dryness: z.number().min(1).max(5).optional(),
    irritation: z.number().min(1).max(5).optional(),
    oiliness: z.number().min(1).max(5).optional(),
    redness: z.number().min(1).max(5).optional(),
    texture: z.number().min(1).max(5).optional(),
    acne: z.number().min(1).max(5).optional(),
    overall: z.number().min(1).max(5).optional(),
});

const createRoutineSchema = z.object({
    date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
    morningProducts: z.array(z.number()).default([]),
    eveningProducts: z.array(z.number()).default([]),
    skinConditionRating: z.number().min(1).max(5).optional(),
    skinConditions: skinConditionSchema.optional(),
    notes: z.string().optional(),
});

export const skincareRoutineRouter = router({
    // Create a new routine entry
    create: protectedProcedure
        .input(createRoutineSchema)
        .mutation(async ({ ctx, input }) => {
            try {
                const {
                    data: { user },
                } = await ctx.supabase.auth.getUser();

                if (!user) {
                    throw new TRPCError({
                        code: "UNAUTHORIZED",
                        message: "User not found",
                    });
                }

                const { data, error } = await ctx.supabase
                    .from("skincare_routine")
                    .insert({
                        user_id: user.id,
                        date: input.date,
                        morning_products: input.morningProducts,
                        evening_products: input.eveningProducts,
                        skin_condition_rating: input.skinConditionRating,
                        skin_conditions: input.skinConditions || null,
                        notes: input.notes || null,
                    })
                    .select()
                    .single();

                if (error) {
                    // Handle duplicate entry
                    if (error.code === "23505") {
                        // Update existing entry instead
                        const { data: updatedData, error: updateError } = await ctx.supabase
                            .from("skincare_routine")
                            .update({
                                morning_products: input.morningProducts,
                                evening_products: input.eveningProducts,
                                skin_condition_rating: input.skinConditionRating,
                                skin_conditions: input.skinConditions || null,
                                notes: input.notes || null,
                            })
                            .eq("user_id", user.id)
                            .eq("date", input.date)
                            .select()
                            .single();

                        if (updateError) {
                            throw new TRPCError({
                                code: "INTERNAL_SERVER_ERROR",
                                message: updateError.message,
                            });
                        }

                        return {
                            id: updatedData.id,
                            date: updatedData.date,
                            morningProducts: updatedData.morning_products || [],
                            eveningProducts: updatedData.evening_products || [],
                            skinConditionRating: updatedData.skin_condition_rating,
                            skinConditions: updatedData.skin_conditions,
                            notes: updatedData.notes,
                            createdAt: updatedData.created_at,
                            updatedAt: updatedData.updated_at,
                        };
                    }

                    throw new TRPCError({
                        code: "INTERNAL_SERVER_ERROR",
                        message: error.message,
                    });
                }

                return {
                    id: data.id,
                    date: data.date,
                    morningProducts: data.morning_products || [],
                    eveningProducts: data.evening_products || [],
                    skinConditionRating: data.skin_condition_rating,
                    skinConditions: data.skin_conditions,
                    notes: data.notes,
                    createdAt: data.created_at,
                    updatedAt: data.updated_at,
                };
            } catch (error) {
                if (error instanceof TRPCError) {
                    throw error;
                }
                console.error("[skincareRoutine.create] Error:", error);
                throw new TRPCError({
                    code: "INTERNAL_SERVER_ERROR",
                    message: "Failed to create skincare routine",
                });
            }
        }),

    // Get all routines for the logged-in user
    getUserRoutines: protectedProcedure.query(async ({ ctx }) => {
        try {
            const {
                data: { user },
            } = await ctx.supabase.auth.getUser();

            if (!user) {
                throw new TRPCError({
                    code: "UNAUTHORIZED",
                    message: "User not found",
                });
            }

            const { data, error } = await ctx.supabase
                .from("skincare_routine")
                .select("*")
                .eq("user_id", user.id)
                .order("date", { ascending: false });

            if (error) {
                throw new TRPCError({
                    code: "INTERNAL_SERVER_ERROR",
                    message: error.message,
                });
            }

            return (data || []).map((routine) => ({
                id: routine.id,
                date: routine.date,
                morningProducts: routine.morning_products || [],
                eveningProducts: routine.evening_products || [],
                skinConditionRating: routine.skin_condition_rating,
                skinConditions: routine.skin_conditions,
                notes: routine.notes,
                createdAt: routine.created_at,
                updatedAt: routine.updated_at,
            }));
        } catch (error) {
            if (error instanceof TRPCError) {
                throw error;
            }
            console.error("[skincareRoutine.getUserRoutines] Error:", error);
            throw new TRPCError({
                code: "INTERNAL_SERVER_ERROR",
                message: "Failed to fetch skincare routines",
            });
        }
    }),

    // Get trend analysis with AI insights
    getTrendAnalysis: protectedProcedure.query(async ({ ctx }) => {
        try {
            const {
                data: { user },
            } = await ctx.supabase.auth.getUser();

            if (!user) {
                throw new TRPCError({
                    code: "UNAUTHORIZED",
                    message: "User not found",
                });
            }

            const { data, error } = await ctx.supabase
                .from("skincare_routine")
                .select("*")
                .eq("user_id", user.id)
                .order("date", { ascending: false });

            if (error) {
                throw new TRPCError({
                    code: "INTERNAL_SERVER_ERROR",
                    message: error.message,
                });
            }

            if (!data || data.length === 0) {
                return {
                    routineCount: 0,
                    analysis: "Start logging your skincare routine to see insights and trends. Track your skin condition over time to identify patterns and improvements.",
                };
            }

            // Calculate basic statistics
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

            // Generate insights based on data
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
        } catch (error) {
            if (error instanceof TRPCError) {
                throw error;
            }
            console.error("[skincareRoutine.getTrendAnalysis] Error:", error);
            throw new TRPCError({
                code: "INTERNAL_SERVER_ERROR",
                message: "Failed to analyze skincare routine trends",
            });
        }
    }),
});

