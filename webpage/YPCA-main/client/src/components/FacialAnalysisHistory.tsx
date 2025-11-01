import { useState, useEffect } from "react";
import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Loader2, ChevronDown, Trash2, Calendar, ShoppingCart } from "lucide-react";
import {
    getFacialAnalysisHistory,
    deleteFacialAnalysisHistory,
    type FacialAnalysisHistory,
} from "@/services/history";
import { supabase } from "@/lib/supabase";
import { useCart } from "@/contexts/CartContext";
import type { Product } from "@/types/product";
import { toast } from "sonner";

export default function FacialAnalysisHistory() {
    const { isAuthenticated } = useAuth();
    const { addItem } = useCart();
    const [history, setHistory] = useState<FacialAnalysisHistory[]>([]);
    const [loading, setLoading] = useState(true);
    const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
    const [productsCache, setProductsCache] = useState<Map<number, Product>>(
        new Map()
    );
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [itemToDelete, setItemToDelete] = useState<string | null>(null);

    useEffect(() => {
        if (isAuthenticated) {
            loadHistory();
        }
    }, [isAuthenticated]);

    const loadHistory = async () => {
        try {
            setLoading(true);
            const data = await getFacialAnalysisHistory();
            setHistory(data);
        } catch (error) {
            console.error("Failed to load history:", error);
            toast.error("Failed to load analysis history");
        } finally {
            setLoading(false);
        }
    };

    const fetchProducts = async (productIds: number[]) => {
        // Check cache first
        const missingIds = productIds.filter((id) => !productsCache.has(id));
        if (missingIds.length === 0) {
            return;
        }

        try {
            const { data, error } = await supabase
                .from("product")
                .select("id, name, brand, description, price, category, main_image_url, stock")
                .in("id", missingIds);

            if (error) throw error;

            const newProducts = new Map(productsCache);
            (data || []).forEach((p: any) => {
                newProducts.set(Number(p.id), {
                    id: String(p.id),
                    name: p.name,
                    brand: p.brand || undefined,
                    category: p.category || undefined,
                    price: p.price,
                    priceCents: Math.round((p.price || 0) * 100),
                    imageUrl: p.main_image_url || undefined,
                    description: p.description || undefined,
                    stock: p.stock || undefined,
                });
            });
            setProductsCache(newProducts);
        } catch (error) {
            console.error("Failed to fetch products:", error);
        }
    };

    const toggleExpanded = (id: string, productIds: number[]) => {
        const newExpanded = new Set(expandedItems);
        if (newExpanded.has(id)) {
            newExpanded.delete(id);
        } else {
            newExpanded.add(id);
            fetchProducts(productIds);
        }
        setExpandedItems(newExpanded);
    };

    const handleDelete = async () => {
        if (!itemToDelete) return;

        try {
            await deleteFacialAnalysisHistory(itemToDelete);
            setHistory(history.filter((item) => item.id !== itemToDelete));
            toast.success("Analysis history deleted");
        } catch (error) {
            console.error("Failed to delete history:", error);
            toast.error("Failed to delete analysis history");
        } finally {
            setDeleteDialogOpen(false);
            setItemToDelete(null);
        }
    };

    const handleAddToCart = (product: Product) => {
        try {
            addItem(product, 1);
            toast.success(`${product.name} added to cart!`);
        } catch (error) {
            toast.error("Failed to add product to cart");
            console.error(error);
        }
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    if (!isAuthenticated) {
        return null;
    }

    if (loading) {
        return (
            <Card>
                <CardContent className="pt-6">
                    <div className="flex items-center justify-center py-8">
                        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (history.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Analysis History</CardTitle>
                </CardHeader>
                <CardContent className="pt-6">
                    <div className="text-center py-8 text-muted-foreground">
                        <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>No analysis history yet.</p>
                        <p className="text-sm mt-2">Your facial analyses will appear here.</p>
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <>
            <Card>
                <CardHeader>
                    <CardTitle>Analysis History</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {history.map((item) => {
                        const isExpanded = expandedItems.has(item.id);
                        const products = item.productIds
                            .map((id) => productsCache.get(id))
                            .filter((p): p is Product => p !== undefined);

                        return (
                            <Collapsible
                                key={item.id}
                                open={isExpanded}
                                onOpenChange={() => toggleExpanded(item.id, item.productIds)}
                            >
                                <Card className="border">
                                    <CollapsibleTrigger asChild>
                                        <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
                                            <div className="flex items-start justify-between">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <Calendar className="w-4 h-4 text-muted-foreground" />
                                                        <span className="text-sm text-muted-foreground">
                                                            {formatDate(item.createdAt)}
                                                        </span>
                                                    </div>
                                                    <CardTitle className="text-base capitalize mb-2">
                                                        {item.skinType || "Unknown"} Skin
                                                    </CardTitle>
                                                    <div className="flex flex-wrap gap-2 mb-2">
                                                        {item.detectedConcerns.slice(0, 3).map((concern, idx) => (
                                                            <span
                                                                key={idx}
                                                                className="px-2 py-1 bg-pink-100 text-pink-700 rounded-full text-xs font-medium"
                                                            >
                                                                {concern}
                                                            </span>
                                                        ))}
                                                        {item.detectedConcerns.length > 3 && (
                                                            <span className="px-2 py-1 text-xs text-muted-foreground">
                                                                +{item.detectedConcerns.length - 3} more
                                                            </span>
                                                        )}
                                                    </div>
                                                    <p className="text-sm text-muted-foreground line-clamp-2">
                                                        {item.analysisResult}
                                                    </p>
                                                    {item.productIds.length > 0 && (
                                                        <p className="text-sm text-muted-foreground mt-2">
                                                            {item.productIds.length} recommended product
                                                            {item.productIds.length !== 1 ? "s" : ""}
                                                        </p>
                                                    )}
                                                </div>
                                                <div className="flex flex-col gap-2 ml-4">
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            setItemToDelete(item.id);
                                                            setDeleteDialogOpen(true);
                                                        }}
                                                        className="text-destructive hover:text-destructive"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </Button>
                                                    <ChevronDown
                                                        className={`w-5 h-5 text-muted-foreground transition-transform ${isExpanded ? "rotate-180" : ""
                                                            }`}
                                                    />
                                                </div>
                                            </div>
                                        </CardHeader>
                                    </CollapsibleTrigger>
                                    <CollapsibleContent>
                                        <CardContent className="pt-0 space-y-4">
                                            <div>
                                                <p className="text-sm text-muted-foreground mb-2">Full Analysis</p>
                                                <p className="text-sm whitespace-pre-wrap">{item.analysisResult}</p>
                                            </div>

                                            {item.inputSkinType && (
                                                <div>
                                                    <p className="text-sm text-muted-foreground mb-1">
                                                        Input Skin Type:{" "}
                                                        <span className="font-medium capitalize">
                                                            {item.inputSkinType}
                                                        </span>
                                                    </p>
                                                </div>
                                            )}

                                            {item.inputConcerns && item.inputConcerns.length > 0 && (
                                                <div>
                                                    <p className="text-sm text-muted-foreground mb-2">
                                                        Input Concerns
                                                    </p>
                                                    <div className="flex flex-wrap gap-2">
                                                        {item.inputConcerns.map((concern, idx) => (
                                                            <span
                                                                key={idx}
                                                                className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-xs"
                                                            >
                                                                {concern}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            {item.budgetRange && (
                                                <div>
                                                    <p className="text-sm text-muted-foreground mb-1">
                                                        Budget Range:{" "}
                                                        <span className="font-medium">
                                                            ${item.budgetRange.min ?? 0} - $
                                                            {item.budgetRange.max ?? "∞"}
                                                        </span>
                                                    </p>
                                                </div>
                                            )}

                                            {products.length > 0 && (
                                                <div>
                                                    <p className="text-sm text-muted-foreground mb-3">
                                                        Recommended Products ({products.length})
                                                    </p>
                                                    <div className="space-y-3 max-h-96 overflow-y-auto">
                                                        {products.map((product) => (
                                                            <div
                                                                key={product.id}
                                                                className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                                                            >
                                                                <div className="flex items-start gap-3">
                                                                    {product.imageUrl && (
                                                                        <img
                                                                            src={product.imageUrl}
                                                                            alt={product.name}
                                                                            className="w-16 h-16 object-cover rounded-md"
                                                                        />
                                                                    )}
                                                                    <div className="flex-1 min-w-0">
                                                                        <p className="font-semibold text-sm truncate">
                                                                            {product.name}
                                                                        </p>
                                                                        {product.brand && (
                                                                            <p className="text-xs text-muted-foreground">
                                                                                {product.brand}
                                                                            </p>
                                                                        )}
                                                                        {product.description && (
                                                                            <p className="text-xs text-gray-600 line-clamp-2 mt-1">
                                                                                {product.description}
                                                                            </p>
                                                                        )}
                                                                        <div className="flex items-center justify-between mt-2">
                                                                            <p className="text-sm font-bold text-pink-600">
                                                                                $
                                                                                {(
                                                                                    product.priceCents
                                                                                        ? product.priceCents / 100
                                                                                        : product.price || 0
                                                                                ).toFixed(2)}
                                                                            </p>
                                                                            {product.stock !== undefined && product.stock > 0 ? (
                                                                                <span className="text-xs text-green-600">
                                                                                    In Stock
                                                                                </span>
                                                                            ) : (
                                                                                <span className="text-xs text-red-600">
                                                                                    Out of Stock
                                                                                </span>
                                                                            )}
                                                                        </div>
                                                                        {item.recommendationReasons?.[product.id] && (
                                                                            <div className="mt-2 p-2 bg-pink-50 rounded text-xs text-gray-700">
                                                                                {Array.isArray(item.recommendationReasons[product.id])
                                                                                    ? item.recommendationReasons[product.id][0]
                                                                                    : item.recommendationReasons[product.id]}
                                                                            </div>
                                                                        )}
                                                                        <Button
                                                                            onClick={() => handleAddToCart(product)}
                                                                            disabled={
                                                                                product.stock !== undefined && product.stock <= 0
                                                                            }
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
                                    </CollapsibleContent>
                                </Card>
                            </Collapsible>
                        );
                    })}
                </CardContent>
            </Card>

            <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete Analysis History?</AlertDialogTitle>
                        <AlertDialogDescription>
                            This action cannot be undone. This will permanently delete this
                            analysis entry from your history.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleDelete}
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    );
}

