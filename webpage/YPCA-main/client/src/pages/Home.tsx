import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Upload, Sparkles, Beaker, TrendingUp, ShoppingCart, ShoppingBag } from "lucide-react";
import { APP_LOGO, APP_TITLE, getLoginUrl } from "@/const";
import { Link } from "wouter";
import { useCart } from "@/contexts/CartContext";

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
      <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-50">
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
            <Card>
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

            <Card>
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

            <Card>
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

            <Card>
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
        <section className="container mx-auto px-4 py-20 bg-white rounded-lg my-20">
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
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-50">
      {/* Dashboard Content */}
      <div className="container mx-auto px-4 py-12">
        <h1 className="text-4xl font-bold mb-12">Welcome to Your Skincare Dashboard</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <Link href="/facial-analysis">
            <Card className="cursor-pointer hover:shadow-lg transition-shadow">
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
            <Card className="cursor-pointer hover:shadow-lg transition-shadow">
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
            <Card className="cursor-pointer hover:shadow-lg transition-shadow">
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
            <Card className="cursor-pointer hover:shadow-lg transition-shadow">
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
      </div>
    </div>
  );
}

