import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Loader2, AlertTriangle, CheckCircle, ArrowLeft } from "lucide-react";
import { Link } from "wouter";
import { toast } from "sonner";
import { fetchProducts } from "@/services/products";
import type { Product } from "@/types/product";

const RECOM_API_URL = import.meta.env.VITE_RECOM_API_URL || "http://localhost:8001";

export default function ConflictAnalyzer() {
  const [selectedProducts, setSelectedProducts] = useState<number[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [productsLoading, setProductsLoading] = useState(true);
  const [productsError, setProductsError] = useState<Error | null>(null);

  // Fetch products from Supabase
  useEffect(() => {
    const loadProducts = async () => {
      try {
        setProductsLoading(true);
        setProductsError(null);
        const data = await fetchProducts();
        setProducts(data);
      } catch (error) {
        console.error("Error fetching products:", error);
        setProductsError(error as Error);
        toast.error("Failed to load products");
      } finally {
        setProductsLoading(false);
      }
    };
    loadProducts();
  }, []);

  const handleProductToggle = (productId: number) => {
    setSelectedProducts((prev) =>
      prev.includes(productId)
        ? prev.filter((id) => id !== productId)
        : [...prev, productId]
    );
  };

  const handleAnalyze = async () => {
    if (selectedProducts.length < 2) {
      toast.error("Please select at least 2 products to analyze");
      return;
    }

    setAnalyzing(true);
    try {
      // Get selected product details with ingredients
      const selectedProductDetails = products.filter((p) =>
        selectedProducts.includes(Number(p.id))
      );

      // Prepare products for LLM analysis
      const productsForAnalysis = selectedProductDetails.map((p) => ({
        id: Number(p.id),
        name: p.name,
        ingredients: p.ingredients || "Not specified",
      }));

      // Call recomsystem API for LLM-based conflict analysis
      const response = await fetch(`${RECOM_API_URL}/api/ingredient-conflict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          products: productsForAnalysis,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Conflict analysis failed: ${response.status} - ${errorText}`);
      }

      const analysisResult = await response.json();
      setResult(analysisResult);
      toast.success("Analysis completed!");
    } catch (error) {
      toast.error("Failed to analyze ingredients");
      console.error(error);
    } finally {
      setAnalyzing(false);
    }
  };

  const selectedProductDetails = products.filter((p) =>
    selectedProducts.includes(Number(p.id))
  );

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
          <h1 className="text-xl font-bold">Ingredient Conflict Analyzer</h1>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Product Selection */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Select Products to Analyze</CardTitle>
                <CardDescription>
                  Choose 2 or more products to check for ingredient conflicts
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {productsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                  </div>
                ) : productsError ? (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-800 font-medium">Error loading products</p>
                    <p className="text-xs text-red-600 mt-1">
                      {productsError.message || "Failed to fetch products"}
                    </p>
                    <p className="text-xs text-red-500 mt-2">
                      Check console for details
                    </p>
                  </div>
                ) : products && products.length > 0 ? (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {products.map((product) => (
                      <div
                        key={product.id}
                        className="flex items-start space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        <Checkbox
                          id={`product-${product.id}`}
                          checked={selectedProducts.includes(Number(product.id))}
                          onCheckedChange={() => handleProductToggle(Number(product.id))}
                          className="mt-1"
                        />
                        <div className="flex-1">
                          <Label
                            htmlFor={`product-${product.id}`}
                            className="cursor-pointer"
                          >
                            <p className="font-semibold">{product.name}</p>
                            <p className="text-sm text-gray-600">{product.brand}</p>
                            {product.ingredients && (
                              <p className="text-xs text-gray-500 mt-1">
                                {typeof product.ingredients === "string"
                                  ? product.ingredients.substring(0, 100)
                                  : "Ingredients available"}
                              </p>
                            )}
                          </Label>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-600 text-center py-8">
                    No products available
                  </p>
                )}

                {/* Selected Products Summary */}
                {selectedProducts.length > 0 && (
                  <div className="mt-6 pt-6 border-t">
                    <p className="text-sm font-medium mb-3">
                      Selected Products ({selectedProducts.length})
                    </p>
                    <div className="space-y-2">
                      {selectedProductDetails.map((product) => (
                        <div
                          key={product.id}
                          className="flex items-center justify-between p-2 bg-pink-50 rounded"
                        >
                          <p className="text-sm font-medium">{product.name}</p>
                          <button
                            onClick={() => handleProductToggle(product.id)}
                            className="text-xs text-pink-600 hover:text-pink-700"
                          >
                            Remove
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Analyze Button */}
                <Button
                  onClick={handleAnalyze}
                  disabled={analyzing || selectedProducts.length < 2}
                  className="w-full bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600 mt-6"
                >
                  {analyzing ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Analyzing Ingredients...
                    </>
                  ) : (
                    "Analyze for Conflicts"
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Analysis Results */}
          <div className="space-y-6">
            {result && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    {result.conflictDetected ? (
                      <>
                        <AlertTriangle className="w-5 h-5 text-red-500" />
                        Conflicts Found
                      </>
                    ) : (
                      <>
                        <CheckCircle className="w-5 h-5 text-green-500" />
                        No Conflicts
                      </>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {result.safetyWarning && (
                    <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <p className="text-sm font-medium text-yellow-800">
                        ⚠️ Safety Warning
                      </p>
                      <p className="text-sm text-yellow-700 mt-1">
                        {result.safetyWarning}
                      </p>
                    </div>
                  )}

                  <div>
                    <p className="text-sm font-medium mb-2">Analysis Summary</p>
                    <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                      <p className="text-sm text-gray-700 leading-relaxed">
                        {result.conflictDetails}
                      </p>
                    </div>
                  </div>

                  {result.alternatives && result.alternatives.length > 0 && (
                    <div>
                      <p className="text-sm font-medium mb-2">
                        💡 Recommendations
                      </p>
                      <div className="space-y-2">
                        {result.alternatives.map((alt: string, idx: number) => (
                          <div
                            key={idx}
                            className="flex items-start gap-2 p-2 bg-blue-50 border border-blue-100 rounded-lg"
                          >
                            <span className="text-blue-500 mt-0.5">✓</span>
                            <span className="text-sm text-gray-700 flex-1">{alt}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {!result.conflictDetected && !result.safetyWarning && (
                    <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-sm text-green-800 font-medium">
                        ✅ Products are safe to use together
                      </p>
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

