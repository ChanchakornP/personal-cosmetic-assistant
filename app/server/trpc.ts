import { initTRPC, TRPCError } from "@trpc/server";
import superjson from "superjson";
import type { Context } from "./context";

const t = initTRPC.context<Context>().create({
    transformer: superjson,
});

export const router = t.router;
export const publicProcedure = t.procedure;

// Middleware to check authentication
const isAuthenticated = t.middleware(async ({ ctx, next }) => {
    try {
        // Get the session token from cookies or Authorization header
        const authHeader = ctx.req.headers.authorization;
        const token = authHeader?.replace("Bearer ", "") || ctx.req.cookies?.["sb-access-token"];

        if (!token) {
            throw new TRPCError({
                code: "UNAUTHORIZED",
                message: "Not authenticated",
            });
        }

        // Verify the token with Supabase
        const {
            data: { user },
            error,
        } = await ctx.supabase.auth.getUser(token);

        if (error || !user) {
            throw new TRPCError({
                code: "UNAUTHORIZED",
                message: "Invalid or expired session",
            });
        }

        return next({
            ctx: {
                ...ctx,
                user,
            },
        });
    } catch (error) {
        if (error instanceof TRPCError) {
            throw error;
        }
        throw new TRPCError({
            code: "UNAUTHORIZED",
            message: "Authentication failed",
        });
    }
});

export const protectedProcedure = t.procedure.use(isAuthenticated);

