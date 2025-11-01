import { APP_LOGO, APP_TITLE } from "@/const";
import { Button } from "@/components/ui/button";
import DashboardLayout from "@/components/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/_core/hooks/useAuth";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { toast } from "sonner";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
});

const registerSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  confirmPassword: z.string().min(6, "Please confirm your password"),
  name: z.string().optional(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type LoginFormValues = z.infer<typeof loginSchema>;
type RegisterFormValues = z.infer<typeof registerSchema>;

function Login() {
  const { signIn, signUp, loading, isAuthenticated, session } = useAuth();
  const [, setLocation] = useLocation();
  const [error, setError] = useState<string | null>(null);
  const [justSignedIn, setJustSignedIn] = useState(false);

  const loginForm = useForm<LoginFormValues>({
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const registerForm = useForm<RegisterFormValues>({
    defaultValues: {
      email: "",
      password: "",
      confirmPassword: "",
      name: "",
    },
  });

  const onLoginSubmit = async (values: LoginFormValues) => {
    try {
      const validated = loginSchema.parse(values);
      setError(null);
      setJustSignedIn(true);

      const result = await signIn(validated.email, validated.password);

      // Verify sign-in was successful
      if (!result?.user || !result?.session) {
        setJustSignedIn(false);
        throw new Error("Sign in completed but no user session was created");
      }

      toast.success("Successfully signed in!");

      // We have a valid session from signIn result, so we can redirect
      // But wait a moment for state to propagate and avoid redirect conflicts
      setJustSignedIn(false);
      setTimeout(() => {
        setLocation("/");
      }, 300); // Give React time to update state

    } catch (err) {
      setJustSignedIn(false);
      if (err instanceof z.ZodError) {
        const firstError = err.issues[0];
        setError(firstError.message);
        toast.error(firstError.message);
      } else {
        const errorMessage = err instanceof Error ? err.message : "Failed to sign in";
        setError(errorMessage);
        toast.error(errorMessage);
      }
    }
  };

  const onRegisterSubmit = async (values: RegisterFormValues) => {
    try {
      const validated = registerSchema.parse(values);
      setError(null);
      await signUp(validated.email, validated.password, validated.name || undefined);
      toast.success("Account created successfully! You are now signed in.");
      setLocation("/");
    } catch (err) {
      if (err instanceof z.ZodError) {
        const firstError = err.issues[0];
        setError(firstError.message);
        toast.error(firstError.message);
      } else {
        const errorMessage = err instanceof Error ? err.message : "Failed to create account";
        setError(errorMessage);
        toast.error(errorMessage);
      }
    }
  };

  // Redirect if already authenticated (but wait a moment to avoid redirect loops)
  // Don't redirect if we just signed in (let onLoginSubmit handle it)
  useEffect(() => {
    if (isAuthenticated && !loading && !justSignedIn) {
      const timer = setTimeout(() => {
        setLocation("/");
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isAuthenticated, loading, justSignedIn, setLocation]);

  return (
    <DashboardLayout>
      <div className="flex flex-1 flex-col items-center justify-center gap-6 py-16 px-4">
        <Card className="glass-card w-full max-w-md border-white/40">
          <div className="flex flex-col items-center gap-6 py-6 px-6">
            <img
              src={APP_LOGO}
              alt={`${APP_TITLE} logo`}
              className="h-20 w-20 rounded-full border border-white/40 shadow-sm"
            />
            <div className="text-center">
              <h1 className="text-3xl font-semibold tracking-tight">
                Welcome to {APP_TITLE}
              </h1>
              <p className="mt-2 text-muted-foreground">
                Sign in or create an account to continue exploring personalized cosmetic insights.
              </p>
            </div>

            <Tabs defaultValue="login" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="login">Sign In</TabsTrigger>
                <TabsTrigger value="register">Sign Up</TabsTrigger>
              </TabsList>

              <TabsContent value="login" className="mt-6">
                <Form {...loginForm}>
                  <form
                    onSubmit={loginForm.handleSubmit(onLoginSubmit)}
                    className="space-y-4"
                  >
                    <FormField
                      control={loginForm.control}
                      name="email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Email</FormLabel>
                          <FormControl>
                            <Input
                              type="email"
                              placeholder="you@example.com"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={loginForm.control}
                      name="password"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Password</FormLabel>
                          <FormControl>
                            <Input
                              type="password"
                              placeholder="Enter your password"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    {error && (
                      <div className="text-sm text-destructive">{error}</div>
                    )}
                    <Button
                      type="submit"
                      className="w-full"
                      size="lg"
                      disabled={loading}
                    >
                      {loading ? "Signing in..." : "Sign In"}
                    </Button>
                  </form>
                </Form>
              </TabsContent>

              <TabsContent value="register" className="mt-6">
                <Form {...registerForm}>
                  <form
                    onSubmit={registerForm.handleSubmit(onRegisterSubmit)}
                    className="space-y-4"
                  >
                    <FormField
                      control={registerForm.control}
                      name="name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Name (Optional)</FormLabel>
                          <FormControl>
                            <Input
                              type="text"
                              placeholder="Your name"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={registerForm.control}
                      name="email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Email</FormLabel>
                          <FormControl>
                            <Input
                              type="email"
                              placeholder="you@example.com"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={registerForm.control}
                      name="password"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Password</FormLabel>
                          <FormControl>
                            <Input
                              type="password"
                              placeholder="At least 6 characters"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={registerForm.control}
                      name="confirmPassword"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Confirm Password</FormLabel>
                          <FormControl>
                            <Input
                              type="password"
                              placeholder="Confirm your password"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    {error && (
                      <div className="text-sm text-destructive">{error}</div>
                    )}
                    <Button
                      type="submit"
                      className="w-full"
                      size="lg"
                      disabled={loading}
                    >
                      {loading ? "Creating account..." : "Create Account"}
                    </Button>
                  </form>
                </Form>
              </TabsContent>
            </Tabs>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}

export default Login;
