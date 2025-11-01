import { useState } from "react";
import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, TrendingUp } from "lucide-react";
import { trpc } from "@/lib/trpc";
import { toast } from "sonner";

export default function RoutineTracker() {
  const { isAuthenticated } = useAuth();
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [skinRating, setSkinRating] = useState(3);
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedProducts, setSelectedProducts] = useState<{
    morning: number[];
    evening: number[];
  }>({ morning: [], evening: [] });

  const productsQuery = trpc.product.list.useQuery();
  const createRoutineMutation = trpc.skincareRoutine.create.useMutation();
  const routinesQuery = trpc.skincareRoutine.getUserRoutines.useQuery(undefined, {
    enabled: isAuthenticated,
  });
  const trendAnalysisQuery = trpc.skincareRoutine.getTrendAnalysis.useQuery(
    undefined,
    { enabled: isAuthenticated }
  );

  const handleAddProduct = (
    productId: number,
    time: "morning" | "evening"
  ) => {
    setSelectedProducts((prev) => ({
      ...prev,
      [time]: prev[time].includes(productId)
        ? prev[time].filter((id) => id !== productId)
        : [...prev[time], productId],
    }));
  };

  const handleSaveRoutine = async () => {
    if (selectedProducts.morning.length === 0 && selectedProducts.evening.length === 0) {
      toast.error("Please select at least one product");
      return;
    }

    setLoading(true);
    try {
      const response = await createRoutineMutation.mutateAsync({
        date,
        morningProducts: selectedProducts.morning,
        eveningProducts: selectedProducts.evening,
        skinConditionRating: skinRating,
        notes,
      });
      toast.success("Routine saved!");
      setNotes("");
      routinesQuery.refetch();
      trendAnalysisQuery.refetch();
    } catch (error) {
      toast.error("Failed to save routine");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const getSelectedProductNames = (ids: number[]) => {
    return ids
      .map((id) => productsQuery.data?.find((p) => p.id === id)?.name)
      .filter(Boolean)
      .join(", ");
  };

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Routine Entry Form */}
          <div className="lg:col-span-2">
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>Log Your Skincare Routine</CardTitle>
                <CardDescription>
                  Record your daily skincare activities and skin condition
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Date */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Date</label>
                  <input
                    type="date"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                  />
                </div>

                {/* Morning Routine */}
                <div className="space-y-3">
                  <h3 className="font-semibold">Morning Routine</h3>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {productsQuery.data?.map((product) => (
                      <label
                        key={`morning-${product.id}`}
                        className="flex items-center gap-3 p-2 hover:bg-gray-50 rounded cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selectedProducts.morning.includes(product.id)}
                          onChange={() => handleAddProduct(product.id, "morning")}
                          className="rounded"
                        />
                        <div>
                          <p className="text-sm font-medium">{product.name}</p>
                          <p className="text-xs text-gray-600">{product.brand}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                  {selectedProducts.morning.length > 0 && (
                    <div className="p-2 bg-blue-50 rounded text-sm text-blue-700">
                      {getSelectedProductNames(selectedProducts.morning)}
                    </div>
                  )}
                </div>

                {/* Evening Routine */}
                <div className="space-y-3">
                  <h3 className="font-semibold">Evening Routine</h3>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {productsQuery.data?.map((product) => (
                      <label
                        key={`evening-${product.id}`}
                        className="flex items-center gap-3 p-2 hover:bg-gray-50 rounded cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selectedProducts.evening.includes(product.id)}
                          onChange={() => handleAddProduct(product.id, "evening")}
                          className="rounded"
                        />
                        <div>
                          <p className="text-sm font-medium">{product.name}</p>
                          <p className="text-xs text-gray-600">{product.brand}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                  {selectedProducts.evening.length > 0 && (
                    <div className="p-2 bg-purple-50 rounded text-sm text-purple-700">
                      {getSelectedProductNames(selectedProducts.evening)}
                    </div>
                  )}
                </div>

                {/* Skin Condition Rating */}
                <div className="space-y-3">
                  <label className="text-sm font-medium">
                    Skin Condition Rating: {skinRating}/5
                  </label>
                  <div className="flex gap-2">
                    {[1, 2, 3, 4, 5].map((rating) => (
                      <button
                        key={rating}
                        onClick={() => setSkinRating(rating)}
                        className={`w-10 h-10 rounded-lg font-semibold transition-colors ${skinRating === rating
                          ? "bg-pink-500 text-white"
                          : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                          }`}
                      >
                        {rating}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Notes */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Notes</label>
                  <Textarea
                    placeholder="Any observations about your skin today? (optional)"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    className="min-h-24"
                  />
                </div>

                {/* Save Button */}
                <Button
                  onClick={handleSaveRoutine}
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    "Save Routine"
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Trends & History */}
          <div className="space-y-6">
            {/* Trend Analysis */}
            {trendAnalysisQuery.data && (
              <Card className="glass-card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-green-500" />
                    Trend Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <p className="text-sm text-gray-600 mb-2">
                      Routines Logged
                    </p>
                    <p className="text-2xl font-bold">
                      {trendAnalysisQuery.data.routineCount}
                    </p>
                  </div>
                  <div className="p-3 bg-blue-50 rounded">
                    <p className="text-sm font-medium mb-2">AI Insights</p>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {trendAnalysisQuery.data.analysis}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Recent Routines */}
            {routinesQuery.data && routinesQuery.data.length > 0 && (
              <Card className="glass-card">
                <CardHeader>
                  <CardTitle className="text-base">Recent Routines</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {routinesQuery.data.slice(0, 5).map((routine: any) => (
                    <div
                      key={routine.id}
                      className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                    >
                      <p className="text-sm font-medium">
                        {new Date(routine.date).toLocaleDateString()}
                      </p>
                      <p className="text-xs text-gray-600 mt-1">
                        Skin Rating: {routine.skinConditionRating}/5
                      </p>
                      {routine.notes && (
                        <p className="text-xs text-gray-700 mt-1 line-clamp-2">
                          {routine.notes}
                        </p>
                      )}
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

