import type { Request, Response } from "express";
import { getSupabaseClient } from "./lib/supabase-server";

export type Context = {
    req: Request;
    res: Response;
    supabase: ReturnType<typeof getSupabaseClient>;
};

export function createContext(opts: { req: Request; res: Response }): Context {
    return {
        req: opts.req,
        res: opts.res,
        supabase: getSupabaseClient(opts.req),
    };
}

