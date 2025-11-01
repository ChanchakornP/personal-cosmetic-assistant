import { useState } from "react";
import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Upload, ShoppingCart } from "lucide-react";
import { analyzeFacialImage, type FacialAnalysisResponse } from "@/services/recom";
import { toast } from "sonner";
import { useCart } from "@/contexts/CartContext";
import type { Product } from "@/types/product";
import { saveFacialAnalysisHistory, extractHistoryData } from "@/services/history";

export default function FacialAnalysis() {
  const { isAuthenticated } = useAuth();
  const { addItem } = useCart();
  const [imageUrl, setImageUrl] = useState("");
  const [skinType, setSkinType] = useState("");
  const [concerns, setConcerns] = useState<string[]>([]);
  const [minPrice, setMinPrice] = useState<string>("");
  const [maxPrice, setMaxPrice] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FacialAnalysisResponse | null>(null);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // In a real app, you'd upload to S3 here
      const reader = new FileReader();
      reader.onload = (event) => {
        setImageUrl(event.target?.result as string);
        toast.success("Image uploaded successfully");
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAnalyze = async () => {
    if (!imageUrl) {
      toast.error("Please upload an image");
      return;
    }

    setLoading(true);
    try {
      // Build budgetRange from user-specified min/max prices
      const budgetRange = (() => {
        const min = minPrice ? parseFloat(minPrice) : undefined;
        const max = maxPrice ? parseFloat(maxPrice) : undefined;

        // Validate that parsed values are valid numbers
        if (minPrice) {
          if (isNaN(min!) || min! < 0) {
            toast.error("Please enter a valid minimum price (must be a number >= 0)");
            setLoading(false);
            return null;
          }
        }
        if (maxPrice) {
          if (isNaN(max!) || max! < 0) {
            toast.error("Please enter a valid maximum price (must be a number >= 0)");
            setLoading(false);
            return null;
          }
        }

        if (min !== undefined && max !== undefined) {
          if (min > max) {
            toast.error("Minimum price cannot be greater than maximum price");
            setLoading(false);
            return null;
          }
          return { min, max };
        } else if (min !== undefined) {
          return { min };
        } else if (max !== undefined) {
          return { max };
        }
        return undefined;
      })();

      if (budgetRange === null) {
        // Validation error occurred
        return;
      }

      const response = await analyzeFacialImage({
        imageUrl,
        skinType: skinType || undefined,
        detectedConcerns: concerns.length > 0 ? concerns : undefined,
        budgetRange,
        limit: 10,
      });
      setResult(response);

      // Save to history
      try {
        const historyData = extractHistoryData(response, {
          skinType: skinType || undefined,
          concerns: concerns.length > 0 ? concerns : undefined,
          budgetRange,
        });
        await saveFacialAnalysisHistory(historyData);
      } catch (historyError) {
        // Don't fail the analysis if history save fails, just log it
        console.warn("Failed to save analysis history:", historyError);
      }

      toast.success("Analysis completed!");
    } catch (error) {
      toast.error("Failed to analyze image");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const toggleConcern = (concern: string) => {
    setConcerns((prev) =>
      prev.includes(concern)
        ? prev.filter((c) => c !== concern)
        : [...prev, concern]
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
      imageUrl: product.mainImageUrl,
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
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Analysis Form */}
          <div className="lg:col-span-2">
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>Upload Your Photo</CardTitle>
                <CardDescription>
                  Upload a clear facial photo for AI-powered skin analysis
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Image Upload */}
                <div className="space-y-2">
                  <Label>Facial Photo</Label>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-pink-500 transition-colors">
                    {imageUrl ? (
                      <div className="space-y-4">
                        <img
                          src={imageUrl}
                          alt="Uploaded"
                          className="max-h-64 mx-auto rounded-lg"
                        />
                        <Button
                          variant="outline"
                          onClick={() => document.getElementById("image-input")?.click()}
                        >
                          Change Image
                        </Button>
                      </div>
                    ) : (
                      <div
                        onClick={() => document.getElementById("image-input")?.click()}
                        className="cursor-pointer"
                      >
                        <Upload className="w-12 h-12 mx-auto text-gray-400 mb-2" />
                        <p className="text-gray-600">
                          Click to upload or drag and drop
                        </p>
                        <p className="text-sm text-gray-500">
                          PNG, JPG, GIF up to 10MB
                        </p>
                      </div>
                    )}
                  </div>
                  <Input
                    id="image-input"
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="hidden"
                  />
                </div>

                {/* Skin Type Selection */}
                <div className="space-y-2">
                  <Label>Skin Type</Label>
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
                  <Label>Skin Concerns</Label>
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
                        className={`p-3 rounded-lg border-2 transition-colors ${concerns.includes(concern)
                          ? "border-pink-500 bg-pink-50"
                          : "border-gray-200 hover:border-pink-300"
                          }`}
                      >
                        <p className="text-sm font-medium">{concern}</p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Price Range */}
                <div className="space-y-2">
                  <Label>Price Range (Optional)</Label>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <Label htmlFor="min-price" className="text-xs text-muted-foreground">
                        Min Price ($)
                      </Label>
                      <Input
                        id="min-price"
                        type="number"
                        placeholder="0.00"
                        min="0"
                        step="0.01"
                        value={minPrice}
                        onChange={(e) => setMinPrice(e.target.value)}
                      />
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor="max-price" className="text-xs text-muted-foreground">
                        Max Price ($)
                      </Label>
                      <Input
                        id="max-price"
                        type="number"
                        placeholder="100.00"
                        min="0"
                        step="0.01"
                        value={maxPrice}
                        onChange={(e) => setMaxPrice(e.target.value)}
                      />
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Leave empty to search all prices. You can specify just min, just max, or both.
                  </p>
                </div>

                {/* Analyze Button */}
                <Button
                  onClick={handleAnalyze}
                  disabled={loading || !imageUrl}
                  className="w-full bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    "Analyze My Skin with AI"
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Analysis Results */}
          <div className="space-y-6">
            {result && (
              <Card className="glass-card">
                <CardHeader>
                  <CardTitle>Analysis Result</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-600 mb-2">Skin Type</p>
                    <p className="font-semibold capitalize">{result.skinType}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-2">Detected Concerns</p>
                    <div className="flex flex-wrap gap-2">
                      {result.detectedConcerns.map((concern, idx) => (
                        <span key={idx} className="px-3 py-1 bg-pink-100 text-pink-700 rounded-full text-xs font-medium">
                          {concern}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-2">Analysis</p>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {result.analysisResult}
                    </p>
                  </div>
                  {result.recommendations && result.recommendations.products.length > 0 && (
                    <div>
                      <p className="text-sm text-gray-600 mb-3">Recommended Products ({result.recommendations.count})</p>
                      <div className="space-y-3 max-h-96 overflow-y-auto">
                        {result.recommendations.products.map((product: any, idx: number) => (
                          <div key={idx} className="p-3 glass-surface rounded-lg hover:shadow-md transition-all">
                            <div className="flex items-start gap-3">
                              {product.mainImageUrl && (
                                <img
                                  src={product.mainImageUrl}
                                  alt={product.name}
                                  className="w-16 h-16 object-cover rounded-md"
                                />
                              )}
                              <div className="flex-1 min-w-0">
                                <p className="font-semibold text-sm truncate">{product.name}</p>
                                {product.description && (
                                  <p className="text-xs text-gray-600 line-clamp-2 mt-1">{product.description}</p>
                                )}
                                <div className="flex items-center justify-between mt-2">
                                  <p className="text-sm font-bold text-pink-600">${product.price?.toFixed(2)}</p>
                                </div>
                                {result.recommendations.reasons && result.recommendations.reasons[product.id] && (
                                  <div className="mt-2 p-2 bg-pink-50 rounded text-xs text-gray-700">
                                    {result.recommendations.reasons[product.id][0]}
                                  </div>
                                )}
                                <Button
                                  onClick={() => handleAddToCart(product)}
                                  className="w-full mt-2"
                                  size="sm"
                                  variant="outline"
                                >
                                  <ShoppingCart className="w-4 h-4 mr-2" />
                                  Add to Cart
                                </Button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

