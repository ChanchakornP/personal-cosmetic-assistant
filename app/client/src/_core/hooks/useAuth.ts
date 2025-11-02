import { getLoginUrl } from "@/const";
import { supabase } from "@/lib/supabase";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { User, Session, AuthError } from "@supabase/supabase-js";

type UseAuthOptions = {
  redirectOnUnauthenticated?: boolean;
  redirectPath?: string;
};

type UserProfile = {
  id: string;
  email?: string;
  emailVerified: boolean;
  name: string;
  avatar?: string;
  createdAt?: string;
};

export function useAuth(options?: UseAuthOptions) {
  const { redirectOnUnauthenticated = false, redirectPath = "/login" } =
    options ?? {};

  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [firstSessionCheckDone, setFirstSessionCheckDone] = useState(false);

  const fetchUserProfile = useCallback(async (userId: string, currentUser?: User | null) => {
    try {
      const { data, error: profileError } = await supabase
        .from("profiles")
        .select("*")
        .eq("id", userId)
        .single();

      if (profileError && profileError.code !== "PGRST116") {
        console.warn("[useAuth] Profile fetch error:", profileError);
      }

      if (data && currentUser) {
        return {
          id: data.id,
          email: data.email || currentUser.email,
          emailVerified: currentUser.email_confirmed_at !== null,
          name: data.name || currentUser.user_metadata?.name || currentUser.email?.split("@")[0] || "User",
          avatar: data.avatar_url,
          createdAt: data.created_at || currentUser.created_at,
          ...data,
        };
      }
      return null;
    } catch (err) {
      console.error("[useAuth] Error fetching profile:", err);
    }
    return null;
  }, []);

  // Initial session load
  useEffect(() => {
    let mounted = true;
    let timeoutId: NodeJS.Timeout;

    // Check if Supabase is properly configured
    const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
    const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseAnonKey || supabaseUrl === "" || supabaseAnonKey === "") {
      console.error("[useAuth] Missing Supabase credentials - authentication disabled");
      setLoading(false);
      setFirstSessionCheckDone(true);
      setSession(null);
      setUser(null);
      setUserProfile(null);
      return;
    }

    const finish = () => {
      if (mounted) {
        setLoading(false);
        setFirstSessionCheckDone(true);
      }
    };

    timeoutId = setTimeout(() => {
      if (mounted && !firstSessionCheckDone) {
        console.warn("[useAuth] Session init taking too long (2s timeout) - continuing");
        finish();
      }
    }, 2000); // Reduced from 5000 to 2000

    const load = async () => {
      try {
        // Add timeout to getSession call itself (faster)
        const sessionPromise = supabase.auth.getSession();
        const timeoutPromise = new Promise((_, reject) =>
          setTimeout(() => reject(new Error("Session check timeout")), 1500) // Reduced from 4000 to 1500
        );

        const result = await Promise.race([sessionPromise, timeoutPromise]);
        const { data: { session }, error } = result as Awaited<ReturnType<typeof supabase.auth.getSession>>;

        if (!mounted) return;
        clearTimeout(timeoutId);

        if (error) {
          console.warn("[useAuth] Session fetch error:", error);
          setError(error as Error);
          setSession(null);
          setUser(null);
          finish();
          return;
        }

        // Check if session is expired
        if (session) {
          const now = Math.floor(Date.now() / 1000);
          const expiresAt = session.expires_at;

          if (expiresAt && expiresAt < now) {
            console.warn("[useAuth] Session expired, clearing");
            await supabase.auth.signOut().catch(() => { });
            setSession(null);
            setUser(null);
            setUserProfile(null);
            finish();
            return;
          }
        }

        setSession(session ?? null);
        setUser(session?.user ?? null);

        if (session?.user) {
          // Don't wait for profile fetch to finish - do it async
          fetchUserProfile(session.user.id, session.user).then((profile) => {
            if (mounted) setUserProfile(profile);
          }).catch(() => { });
        }

        finish();
      } catch (err) {
        if (!mounted) return;
        clearTimeout(timeoutId);
        if (err instanceof Error && err.message === "Session check timeout") {
          console.warn("[useAuth] Session check timed out after 1.5s");
          // On timeout, check localStorage for cached session
          const cachedSession = localStorage.getItem("supabase.auth.token");
          if (!cachedSession) {
            setSession(null);
            setUser(null);
          }
        } else {
          console.error("[useAuth] Session check failed:", err);
        }
        setError(err instanceof Error ? err : new Error(String(err)));
        finish();
      }
    };

    load();

    const { data: { subscription } } =
      supabase.auth.onAuthStateChange(async (event, newSession) => {
        if (!mounted) return;

        // Mark session check as done when auth state changes
        if (!firstSessionCheckDone) {
          setFirstSessionCheckDone(true);
        }

        // Check if session is expired
        if (newSession) {
          const now = Math.floor(Date.now() / 1000);
          const expiresAt = newSession.expires_at;

          if (expiresAt && expiresAt < now) {
            console.warn("[useAuth] Session expired in state change, signing out");
            await supabase.auth.signOut().catch(() => { });
            setSession(null);
            setUser(null);
            setUserProfile(null);
            setLoading(false);
            return;
          }
        }

        setSession(newSession);
        setUser(newSession?.user ?? null);
        setLoading(false);

        if (newSession?.user) {
          // Fetch profile async - don't block state update
          fetchUserProfile(newSession.user.id, newSession.user).then((profile) => {
            if (mounted) setUserProfile(profile);
          }).catch(() => { });
        } else {
          setUserProfile(null);
        }
      });

    return () => {
      mounted = false;
      clearTimeout(timeoutId);
      subscription.unsubscribe();
    };
  }, [fetchUserProfile, firstSessionCheckDone]);

  const signIn = useCallback(async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) throw error;

      // Update state immediately after successful sign in
      if (data.user && data.session) {
        // Check session expiration
        const now = Math.floor(Date.now() / 1000);
        const expiresAt = data.session.expires_at;

        if (expiresAt && expiresAt < now) {
          console.warn("[useAuth] New session is already expired");
          await supabase.auth.signOut().catch(() => { });
          throw new Error("Session expired immediately after sign in");
        }

        setSession(data.session);
        setUser(data.user);
        setFirstSessionCheckDone(true);
        setLoading(false); // Set loading to false immediately

        // Fetch profile async - don't block
        fetchUserProfile(data.user.id, data.user).then((profile) => {
          setUserProfile(profile);
        }).catch(() => { });
      }

      return data;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      setLoading(false);
      throw error;
    }
  }, [fetchUserProfile]);

  const signUp = useCallback(async (email: string, password: string, name?: string) => {
    setLoading(true);
    setError(null);
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: { data: { name: name || email.split("@")[0] } }
      });

      if (error) throw error;

      if (data.user) {
        // Create profile entry
        const { error: profileError } = await supabase.from("profiles").insert({
          id: data.user.id,
          email,
          name: name || email.split("@")[0],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });

        if (profileError) {
          console.warn("[useAuth] Profile creation error:", profileError);
          // Don't throw - user is created, profile can be fixed later
        }

        const profile = await fetchUserProfile(data.user.id, data.user);
        setUserProfile(profile);
      }

      return data;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [fetchUserProfile]);

  const logout = useCallback(async () => {
    setLoading(true);
    try {
      await supabase.auth.signOut();
      setUser(null);
      setSession(null);
      setUserProfile(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    if (user?.id) {
      const profile = await fetchUserProfile(user.id, user);
      setUserProfile(profile);
    }
  }, [user, fetchUserProfile]);

  const state = useMemo(() => {
    const display = userProfile || (user ? {
      id: user.id,
      email: user.email,
      emailVerified: user.email_confirmed_at !== null,
      name: user.user_metadata?.name || user.email?.split("@")[0] || "User",
      avatar: user.user_metadata?.avatar_url,
      createdAt: user.created_at,
    } : null);

    if (display && session) {
      localStorage.setItem("pca-user-info", JSON.stringify(display));
    } else {
      localStorage.removeItem("pca-user-info");
    }

    return {
      user: display,
      loading,
      error,
      isAuthenticated: Boolean(user),
    };
  }, [user, userProfile, loading, error, session]);

  // redirect only once session is confirmed null
  useEffect(() => {
    if (!redirectOnUnauthenticated) return;
    if (loading) return;
    if (!firstSessionCheckDone) return;

    if (!user && typeof window !== "undefined" && window.location.pathname !== redirectPath) {
      window.location.href = redirectPath;
    }
  }, [redirectOnUnauthenticated, redirectPath, firstSessionCheckDone, loading, user]);

  return { ...state, session, refresh, logout, signIn, signUp };
}
