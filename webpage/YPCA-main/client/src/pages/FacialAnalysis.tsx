import { useState } from "react";
import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Upload, ArrowLeft } from "lucide-react";
import { Link } from "wouter";
import { trpc } from "@/lib/trpc";
import { toast } from "sonner";

export default function FacialAnalysis() {
  const { isAuthenticated } = useAuth();
  const [imageUrl, setImageUrl] = useState("");
  const [skinType, setSkinType] = useState("");
  const [concerns, setConcerns] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const createAnalysisMutation = trpc.facialAnalysis.create.useMutation();
  const analysisQuery = trpc.facialAnalysis.getUserAnalysis.useQuery(undefined, {
    enabled: isAuthenticated,
  });

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
    if (!imageUrl || !skinType) {
      toast.error("Please upload an image and select a skin type");
      return;
    }

    setLoading(true);
    try {
      const response = await createAnalysisMutation.mutateAsync({
        imageUrl,
        skinType,
        detectedConcerns: concerns,
      });
      setResult(response);
      toast.success("Analysis completed!");
      // Refresh the analysis list
      analysisQuery.refetch();
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
          <h1 className="text-xl font-bold">Facial Analysis</h1>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Analysis Form */}
          <div className="lg:col-span-2">
            <Card>
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
                        className={`p-3 rounded-lg border-2 transition-colors ${
                          concerns.includes(concern)
                            ? "border-pink-500 bg-pink-50"
                            : "border-gray-200 hover:border-pink-300"
                        }`}
                      >
                        <p className="text-sm font-medium">{concern}</p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Analyze Button */}
                <Button
                  onClick={handleAnalyze}
                  disabled={loading || !imageUrl || !skinType}
                  className="w-full bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    "Analyze My Skin"
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
                  <CardTitle>Analysis Result</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-600 mb-2">Skin Type</p>
                    <p className="font-semibold capitalize">{result.skinType}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-2">Analysis</p>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {result.analysisResult}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Previous Analyses */}
            {analysisQuery.data && analysisQuery.data.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Previous Analyses</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {analysisQuery.data.slice(0, 5).map((analysis: any) => (
                    <div
                      key={analysis.id}
                      className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                    >
                      <p className="text-sm font-medium">
                        {new Date(analysis.createdAt).toLocaleDateString()}
                      </p>
                      <p className="text-xs text-gray-600 capitalize">
                        {analysis.skinType} skin
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

