import { z } from "zod";
import { router, publicProcedure, protectedProcedure } from "../trpc";
import { supabaseAdmin, getSupabaseClient } from "../lib/supabase-server";

export const authRouter = router({
    me: protectedProcedure.query(async ({ ctx }) => {
        try {
            const {
                data: { user },
                error,
            } = await ctx.supabase.auth.getUser();

            if (error || !user) {
                return null;
            }

            // Optionally fetch additional user profile data from a profiles table
            const { data: profile } = await ctx.supabase
                .from("profiles")
                .select("*")
                .eq("id", user.id)
                .single();

            return {
                id: user.id,
                email: user.email,
                emailVerified: user.email_confirmed_at !== null,
                name: profile?.name || user.user_metadata?.name || user.email?.split("@")[0] || "User",
                avatar: profile?.avatar_url || user.user_metadata?.avatar_url,
                createdAt: user.created_at,
                ...profile,
            };
        } catch (error) {
            console.error("[auth.me] Error:", error);
            return null;
        }
    }),

    signUp: publicProcedure
        .input(
            z.object({
                email: z.string().email("Invalid email address"),
                password: z.string().min(6, "Password must be at least 6 characters"),
                name: z.string().optional(),
            })
        )
        .mutation(async ({ input }) => {
            try {
                const { data, error } = await supabaseAdmin.auth.signUp({
                    email: input.email,
                    password: input.password,
                    options: {
                        data: {
                            name: input.name || input.email.split("@")[0],
                        },
                    },
                });

                if (error) {
                    throw new Error(error.message);
                }

                if (!data.user) {
                    throw new Error("Failed to create user");
                }

                // Create profile entry
                const { error: profileError } = await supabaseAdmin.from("profiles").insert({
                    id: data.user.id,
                    email: input.email,
                    name: input.name || input.email.split("@")[0],
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                });

                if (profileError) {
                    console.error("[auth.signUp] Profile creation error:", profileError);
                    // Don't throw - user is created, profile can be fixed later
                }

                return {
                    user: data.user,
                    session: data.session,
                };
            } catch (error) {
                console.error("[auth.signUp] Error:", error);
                throw error;
            }
        }),

    signIn: publicProcedure
        .input(
            z.object({
                email: z.string().email("Invalid email address"),
                password: z.string().min(1, "Password is required"),
            })
        )
        .mutation(async ({ input }) => {
            try {
                const { data, error } = await supabaseAdmin.auth.signInWithPassword({
                    email: input.email,
                    password: input.password,
                });

                if (error) {
                    throw new Error(error.message);
                }

                if (!data.session) {
                    throw new Error("Failed to create session");
                }

                return {
                    session: data.session,
                    user: data.user,
                };
            } catch (error) {
                console.error("[auth.signIn] Error:", error);
                throw error;
            }
        }),

    signOut: protectedProcedure.mutation(async ({ ctx }) => {
        try {
            const { error } = await ctx.supabase.auth.signOut();
            if (error) {
                throw new Error(error.message);
            }
            return { success: true };
        } catch (error) {
            console.error("[auth.signOut] Error:", error);
            throw error;
        }
    }),

    logout: protectedProcedure.mutation(async ({ ctx }) => {
        try {
            const { error } = await ctx.supabase.auth.signOut();
            if (error) {
                throw new Error(error.message);
            }
            return { success: true };
        } catch (error) {
            console.error("[auth.logout] Error:", error);
            throw error;
        }
    }),
});

