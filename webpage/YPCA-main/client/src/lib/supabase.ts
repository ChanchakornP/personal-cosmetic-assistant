import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
    console.warn(
        "Missing Supabase environment variables: VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY"
    );
}

export const supabase = createClient(
    supabaseUrl || "",
    supabaseAnonKey || "",
    {
        auth: {
            autoRefreshToken: true,
            persistSession: true,
            detectSessionInUrl: true,
            storage: window.localStorage,
            storageKey: "supabase.auth.token",
            // Automatically handle token refresh failures
            flowType: "pkce",
        },
    }
);

// Note: Global auth state change listener removed to avoid duplicate checks
// Each component that needs auth state should use useAuth hook instead

