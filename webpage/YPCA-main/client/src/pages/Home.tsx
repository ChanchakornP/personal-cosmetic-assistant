import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Upload, Sparkles, Beaker, TrendingUp, ShoppingCart, ShoppingBag, ArrowRight } from "lucide-react";
import { APP_LOGO, APP_TITLE, getLoginUrl } from "@/const";
import { Link } from "wouter";
import { useCart } from "@/contexts/CartContext";
import FacialAnalysisHistory from "@/components/FacialAnalysisHistory";

export default function Home() {
  const { user, loading, isAuthenticated } = useAuth();
  const { items: cartItems } = useCart();
  const cartItemCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="animate-spin w-8 h-8" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen">
        {/* Hero Section */}
        <section className="container mx-auto px-4 py-20">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="text-5xl font-bold text-gray-900 mb-6">
              Your Personal Cosmetic Assistant
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              Discover personalized skincare recommendations powered by advanced AI.
              Get expert analysis of your skin, detect ingredient conflicts, and build
              the perfect skincare routine tailored just for you.
            </p>
            <Button
              size="lg"
              onClick={() => (window.location.href = getLoginUrl())}
              className="bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600"
            >
              Get Started Free
            </Button>
          </div>
        </section>

        {/* Features Section */}
        <section className="container mx-auto px-4 py-20">
          <h2 className="text-3xl font-bold text-center mb-12">Key Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="glass-card">
              <CardHeader>
                <Upload className="w-8 h-8 text-pink-500 mb-2" />
                <CardTitle>Facial Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Upload your photo and get instant AI-powered skin analysis including skin type and concerns.
                </p>
              </CardContent>
            </Card>

            <Card className="glass-card">
              <CardHeader>
                <Sparkles className="w-8 h-8 text-purple-500 mb-2" />
                <CardTitle>Smart Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Receive personalized product recommendations based on your unique skin profile.
                </p>
              </CardContent>
            </Card>

            <Card className="glass-card">
              <CardHeader>
                <Beaker className="w-8 h-8 text-blue-500 mb-2" />
                <CardTitle>Conflict Detection</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Identify potential ingredient conflicts to avoid allergies and skin reactions.
                </p>
              </CardContent>
            </Card>

            <Card className="glass-card">
              <CardHeader>
                <TrendingUp className="w-8 h-8 text-green-500 mb-2" />
                <CardTitle>Progress Tracking</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Monitor your skincare routine and track improvements over time with detailed analytics.
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* How It Works */}
        <section className="container mx-auto px-4 py-20 glass-card rounded-lg my-20">
          <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="bg-pink-100 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-4">
                <span className="text-pink-600 font-bold text-lg">1</span>
              </div>
              <h3 className="font-bold text-lg mb-2">Upload Photo</h3>
              <p className="text-gray-600">
                Take or upload a clear photo of your face for analysis.
              </p>
            </div>
            <div className="text-center">
              <div className="bg-purple-100 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-4">
                <span className="text-purple-600 font-bold text-lg">2</span>
              </div>
              <h3 className="font-bold text-lg mb-2">AI Analysis</h3>
              <p className="text-gray-600">
                Our AI analyzes your skin type, concerns, and condition.
              </p>
            </div>
            <div className="text-center">
              <div className="bg-blue-100 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-4">
                <span className="text-blue-600 font-bold text-lg">3</span>
              </div>
              <h3 className="font-bold text-lg mb-2">Get Recommendations</h3>
              <p className="text-gray-600">
                Receive personalized product recommendations and skincare tips.
              </p>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="container mx-auto px-4 py-20 text-center">
          <h2 className="text-3xl font-bold mb-6">Ready to Transform Your Skincare?</h2>
          <Button
            size="lg"
            onClick={() => (window.location.href = getLoginUrl())}
            className="bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600"
          >
            Start Your Free Analysis
          </Button>
        </section>
      </div>
    );
  }

  // Authenticated user dashboard
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="container mx-auto px-4 pt-12 pb-8">
        <Card className="glass-card overflow-hidden border-white/40">
          <CardContent className="p-8 md:p-12">
            <div className="flex flex-col md:flex-row items-center md:items-start gap-8">
              {/* Left side - Text content */}
              <div className="flex-1 text-center md:text-left">
                <div className="flex items-center gap-2 justify-center md:justify-start mb-4">
                  <Sparkles className="w-6 h-6 text-yellow-500" />
                </div>
                <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-4">
                  Welcome back{user?.name ? `, ${user.name.split(' ')[0]}` : ''}!
                </h1>
                <p className="text-lg md:text-xl text-gray-700 mb-8 max-w-2xl mx-auto md:mx-0">
                  Discover your perfect skincare routine with AI-powered analysis.
                  Get personalized recommendations tailored to your unique skin profile.
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center md:justify-start">
                  <Link href="/facial-analysis">
                    <Button
                      size="lg"
                      className="w-full sm:w-auto text-base px-8 py-6 font-semibold shadow-lg hover:shadow-xl transition-all"
                    >
                      <Upload className="w-5 h-5 mr-2" />
                      Analyze My Skin
                      <ArrowRight className="w-5 h-5 ml-2" />
                    </Button>
                  </Link>
                  <Link href="/products">
                    <Button
                      variant="outline"
                      size="lg"
                      className="w-full sm:w-auto text-base px-8 py-6 font-semibold glass-surface hover:shadow-lg transition-all border-white/40"
                    >
                      <ShoppingBag className="w-5 h-5 mr-2" />
                      Browse Products
                    </Button>
                  </Link>
                </div>
              </div>

              {/* Right side - Decorative elements */}
              <div className="hidden lg:flex items-center justify-center w-48 h-48">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-br from-yellow-500/20 to-yellow-500/5 rounded-full blur-3xl"></div>
                  <div className="relative bg-white/30 backdrop-blur-sm rounded-full w-32 h-32 flex items-center justify-center border border-white/40">
                    <Sparkles className="w-16 h-16 text-yellow-500/60" />
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Dashboard Content */}
      <div className="container mx-auto px-4 py-8">
        <h2 className="text-3xl font-bold mb-8 text-center md:text-left">Quick Actions</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <Link href="/facial-analysis">
            <Card className="glass-card cursor-pointer hover:shadow-xl transition-all hover:scale-[1.02]">
              <CardHeader>
                <Upload className="w-8 h-8 text-pink-500 mb-2" />
                <CardTitle>Facial Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Analyze your skin with AI-powered facial recognition
                </p>
              </CardContent>
            </Card>
          </Link>

          <Link href="/conflict-analyzer">
            <Card className="glass-card cursor-pointer hover:shadow-xl transition-all hover:scale-[1.02]">
              <CardHeader>
                <Beaker className="w-8 h-8 text-blue-500 mb-2" />
                <CardTitle>Conflict Analyzer</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Check for ingredient conflicts and allergies
                </p>
              </CardContent>
            </Card>
          </Link>

          <Link href="/routine-tracker">
            <Card className="glass-card cursor-pointer hover:shadow-xl transition-all hover:scale-[1.02]">
              <CardHeader>
                <TrendingUp className="w-8 h-8 text-green-500 mb-2" />
                <CardTitle>Routine Tracker</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Track your daily skincare routine and progress
                </p>
              </CardContent>
            </Card>
          </Link>

          <Link href="/products">
            <Card className="glass-card cursor-pointer hover:shadow-xl transition-all hover:scale-[1.02]">
              <CardHeader>
                <ShoppingBag className="w-8 h-8 text-orange-500 mb-2" />
                <CardTitle>Products</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Browse and shop our complete skincare product catalog
                </p>
              </CardContent>
            </Card>
          </Link>
        </div>

        {/* Analysis History */}
        <div className="mt-12">
          <FacialAnalysisHistory />
        </div>
      </div>
    </div>
  );
}

