import { useState } from "react";
import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Loader2, AlertTriangle, CheckCircle, ArrowLeft } from "lucide-react";
import { Link } from "wouter";
import { trpc } from "@/lib/trpc";
import { toast } from "sonner";

export default function ConflictAnalyzer() {
  const { isAuthenticated } = useAuth();
  const [selectedProducts, setSelectedProducts] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const productsQuery = trpc.product.list.useQuery();
  const analyzeConflictMutation = trpc.ingredientConflict.analyze.useMutation();
  const conflictsQuery = trpc.ingredientConflict.getUserConflicts.useQuery(undefined, {
    enabled: isAuthenticated,
  });

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

    setLoading(true);
    try {
      const response = await analyzeConflictMutation.mutateAsync({
        productIds: selectedProducts,
      });
      setResult(response);
      toast.success("Analysis completed!");
      conflictsQuery.refetch();
    } catch (error) {
      toast.error("Failed to analyze ingredients");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const selectedProductDetails = productsQuery.data?.filter((p) =>
    selectedProducts.includes(p.id)
  ) || [];

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
                {productsQuery.isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                  </div>
                ) : productsQuery.data && productsQuery.data.length > 0 ? (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {productsQuery.data.map((product) => (
                      <div
                        key={product.id}
                        className="flex items-start space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        <Checkbox
                          id={`product-${product.id}`}
                          checked={selectedProducts.includes(product.id)}
                          onCheckedChange={() => handleProductToggle(product.id)}
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
                  disabled={loading || selectedProducts.length < 2}
                  className="w-full bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600 mt-6"
                >
                  {loading ? (
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
                        Safety Warning
                      </p>
                      <p className="text-sm text-yellow-700 mt-1">
                        {result.safetyWarning}
                      </p>
                    </div>
                  )}

                  <div>
                    <p className="text-sm font-medium mb-2">Detailed Analysis</p>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {result.conflictDetails}
                    </p>
                  </div>

                  {result.alternatives && result.alternatives.length > 0 && (
                    <div>
                      <p className="text-sm font-medium mb-2">
                        Alternative Suggestions
                      </p>
                      <ul className="text-sm text-gray-700 space-y-1">
                        {result.alternatives.map((alt: string, idx: number) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-pink-500 mt-1">•</span>
                            <span>{alt}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Previous Analyses */}
            {conflictsQuery.data && conflictsQuery.data.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Analysis History</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {conflictsQuery.data.slice(0, 5).map((conflict: any) => (
                    <div
                      key={conflict.id}
                      className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        {conflict.conflictDetected ? (
                          <AlertTriangle className="w-4 h-4 text-red-500" />
                        ) : (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        )}
                        <p className="text-sm font-medium">
                          {new Date(conflict.createdAt).toLocaleDateString()}
                        </p>
                      </div>
                      <p className="text-xs text-gray-600">
                        {conflict.conflictDetected
                          ? "Conflicts detected"
                          : "No conflicts"}
                      </p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

