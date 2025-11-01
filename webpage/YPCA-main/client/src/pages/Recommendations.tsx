import { useState } from "react";
import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Sparkles, ArrowLeft, Heart, ShoppingCart } from "lucide-react";
import { Link } from "wouter";
import { getRecommendations } from "@/services/recom";
import { toast } from "sonner";
import { useCart } from "@/contexts/CartContext";
import type { Product } from "@/types/product";

export default function Recommendations() {
  const { isAuthenticated } = useAuth();
  const { addItem } = useCart();
  const [skinType, setSkinType] = useState("");
  const [concerns, setConcerns] = useState<string[]>([]);
  const [budget, setBudget] = useState("");
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [savedProducts, setSavedProducts] = useState<number[]>([]);

  // Legacy TRPC calls removed; using direct recomsystem API

  const toggleConcern = (concern: string) => {
    setConcerns((prev) =>
      prev.includes(concern)
        ? prev.filter((c) => c !== concern)
        : [...prev, concern]
    );
  };

  const handleGenerateRecommendations = async () => {
    if (!skinType || concerns.length === 0) {
      toast.error("Please select skin type and at least one concern");
      return;
    }

    setLoading(true);
    try {
      const budgetRange = (() => {
        if (budget === "budget") return { min: 0, max: 20 };
        if (budget === "mid") return { min: 20, max: 50 };
        if (budget === "premium") return { min: 50, max: 100 };
        if (budget === "luxury") return { min: 100 };
        return undefined;
      })();

      const response = await getRecommendations({
        skinProfile: {
          skinType,
          concerns,
          budgetRange,
        },
        limit: 10,
        strategy: "hybrid",
      });
      setRecommendations(response);
      toast.success("Recommendations generated!");
    } catch (error) {
      toast.error("Failed to generate recommendations");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSaveProduct = (productId: number) => {
    setSavedProducts((prev) =>
      prev.includes(productId)
        ? prev.filter((id) => id !== productId)
        : [...prev, productId]
    );
  };

  // Convert recommendation product to Product type for cart
  const convertToProduct = (product: any): Product => {
    return {
      id: product.id,
      name: product.name,
      brand: product.brand,
      category: product.category,
      priceCents: product.price ? Math.round(product.price * 100) : undefined,
      price: product.price,
      imageUrl: product.mainImageUrl || product.imageUrl,
      description: product.description,
      stock: product.stock,
      ingredients: product.ingredients,
    };
  };

  const handleAddToCart = (product: any) => {
    try {
      const cartProduct = convertToProduct(product);
      addItem(cartProduct, 1);
      toast.success(`${product.name} added to cart!`);
    } catch (error) {
      toast.error("Failed to add product to cart");
      console.error(error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-50">
      {/* Navigation */}
      <nav className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center gap-4">
          <Link href="/">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </Link>
          <h1 className="text-xl font-bold">Product Recommendations</h1>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Preference Form */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Get Personalized Recommendations</CardTitle>
                <CardDescription>
                  Tell us about your skin and preferences
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Skin Type */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Skin Type</label>
                  <Select value={skinType} onValueChange={setSkinType}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select your skin type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="oily">Oily</SelectItem>
                      <SelectItem value="dry">Dry</SelectItem>
                      <SelectItem value="combination">Combination</SelectItem>
                      <SelectItem value="sensitive">Sensitive</SelectItem>
                      <SelectItem value="normal">Normal</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Skin Concerns */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Skin Concerns</label>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      "Acne",
                      "Wrinkles",
                      "Dark Spots",
                      "Sensitivity",
                      "Dryness",
                      "Oiliness",
                      "Redness",
                      "Texture",
                    ].map((concern) => (
                      <button
                        key={concern}
                        onClick={() => toggleConcern(concern)}
                        className={`p-3 rounded-lg border-2 transition-colors text-left ${concerns.includes(concern)
                          ? "border-pink-500 bg-pink-50"
                          : "border-gray-200 hover:border-pink-300"
                          }`}
                      >
                        <p className="text-sm font-medium">{concern}</p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Budget */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Budget Range</label>
                  <Select value={budget} onValueChange={setBudget}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select budget range" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="budget">Budget ($0-$20)</SelectItem>
                      <SelectItem value="mid">Mid-range ($20-$50)</SelectItem>
                      <SelectItem value="premium">Premium ($50-$100)</SelectItem>
                      <SelectItem value="luxury">Luxury ($100+)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Generate Button */}
                <Button
                  onClick={handleGenerateRecommendations}
                  disabled={loading || !skinType || concerns.length === 0}
                  className="w-full bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Generate Recommendations
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Recommendations Results */}
          <div className="space-y-6">
            {recommendations && recommendations.products && (
              <div className="space-y-4">
                <h3 className="font-bold text-lg">Recommended Products</h3>
                {recommendations.products.map((product: any) => (
                  <Card key={product.id}>
                    <CardContent className="pt-6">
                      <div className="space-y-3">
                        <div>
                          <p className="font-semibold">{product.name}</p>
                          <p className="text-sm text-gray-600">{product.brand}</p>
                        </div>
                        {product.price && (
                          <p className="text-lg font-bold text-pink-600">
                            ${product.price}
                          </p>
                        )}
                        <p className="text-sm text-gray-700">
                          {product.description}
                        </p>
                        <div className="flex gap-2">
                          <button
                            onClick={() => toggleSaveProduct(product.id)}
                            className={`flex-1 p-2 rounded-lg transition-colors flex items-center justify-center gap-2 ${savedProducts.includes(product.id)
                              ? "bg-pink-100 text-pink-600"
                              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                              }`}
                          >
                            <Heart
                              className={`w-4 h-4 ${savedProducts.includes(product.id)
                                ? "fill-current"
                                : ""
                                }`}
                            />
                            {savedProducts.includes(product.id)
                              ? "Saved"
                              : "Save"}
                          </button>
                          <Button
                            onClick={() => handleAddToCart(product)}
                            disabled={product.stock !== undefined && product.stock <= 0}
                            className="flex-1"
                            size="sm"
                            variant="outline"
                          >
                            <ShoppingCart className="w-4 h-4 mr-2" />
                            Add to Cart
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}

                {recommendations.recommendations && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Why These?</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {recommendations.recommendations}
                      </p>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}

            {/* Saved Products */}
            {savedProducts.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">
                    Saved Products ({savedProducts.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600">
                    You have saved {savedProducts.length} product(s) for later
                    review.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

