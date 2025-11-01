import ProductCard from "../components/ProductCard";
import { fetchProducts } from "../services/products";
import { useQuery } from "@tanstack/react-query";
import { Spinner } from "../components/ui/spinner";

export default function ProductsPage() {
    const { data, isLoading, error } = useQuery({
        queryKey: ["products"],
        queryFn: fetchProducts,
    });

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-50">
                <div className="w-full flex justify-center py-20">
                    <Spinner className="size-8" />
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-50">
                <div className="w-full flex justify-center py-20 text-destructive">
                    Failed to load products
                </div>
            </div>
        );
    }

    const products = data ?? [];

    return (
        <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-50">

            {/* Products Content */}
            <div className="container mx-auto px-4 py-8">
                <h1 className="text-2xl font-semibold mb-6">Products</h1>
                {products.length === 0 ? (
                    <div className="text-muted-foreground">No products available.</div>
                ) : (
                    <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
                        {products.map((p) => (
                            <ProductCard key={p.id} product={p} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}


