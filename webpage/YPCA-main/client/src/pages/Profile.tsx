import { useState } from "react";
import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, ArrowLeft, LogOut } from "lucide-react";
import { Link } from "wouter";
import { trpc } from "@/lib/trpc";
import { toast } from "sonner";

export default function Profile() {
  const { user, logout } = useAuth();
  const [skinType, setSkinType] = useState("");
  const [budget, setBudget] = useState("");
  const [allergies, setAllergies] = useState<string[]>([]);
  const [concerns, setConcerns] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const userProfileQuery = trpc.userProfile.get.useQuery();
  const updateProfileMutation = trpc.userProfile.update.useMutation();

  const toggleAllergy = (allergy: string) => {
    setAllergies((prev) =>
      prev.includes(allergy)
        ? prev.filter((a) => a !== allergy)
        : [...prev, allergy]
    );
  };

  const toggleConcern = (concern: string) => {
    setConcerns((prev) =>
      prev.includes(concern)
        ? prev.filter((c) => c !== concern)
        : [...prev, concern]
    );
  };

  const handleSaveProfile = async () => {
    setLoading(true);
    try {
      await updateProfileMutation.mutateAsync({
        skinType,
        budget,
        allergies,
        skinConcerns: concerns,
      });
      toast.success("Profile updated!");
      userProfileQuery.refetch();
    } catch (error) {
      toast.error("Failed to update profile");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    toast.success("Logged out successfully");
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
          <h1 className="text-xl font-bold">User Profile</h1>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-12">
        <div className="max-w-2xl">
          {/* User Info */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Account Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-gray-600 mb-1">Name</p>
                <p className="text-lg font-semibold">{user?.name || "Not set"}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Email</p>
                <p className="text-lg font-semibold">{user?.email || "Not set"}</p>
              </div>
            </CardContent>
          </Card>

          {/* Skin Profile */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Skin Profile</CardTitle>
              <CardDescription>
                Help us personalize your recommendations
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

              {/* Allergies */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Known Allergies</label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    "Fragrance",
                    "Alcohol",
                    "Parabens",
                    "Sulfates",
                    "Nut oils",
                    "Latex",
                  ].map((allergy) => (
                    <button
                      key={allergy}
                      onClick={() => toggleAllergy(allergy)}
                      className={`p-3 rounded-lg border-2 transition-colors text-left ${
                        allergies.includes(allergy)
                          ? "border-pink-500 bg-pink-50"
                          : "border-gray-200 hover:border-pink-300"
                      }`}
                    >
                      <p className="text-sm font-medium">{allergy}</p>
                    </button>
                  ))}
                </div>
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
                      className={`p-3 rounded-lg border-2 transition-colors text-left ${
                        concerns.includes(concern)
                          ? "border-purple-500 bg-purple-50"
                          : "border-gray-200 hover:border-purple-300"
                      }`}
                    >
                      <p className="text-sm font-medium">{concern}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Save Button */}
              <Button
                onClick={handleSaveProfile}
                disabled={loading}
                className="w-full bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  "Save Profile"
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Logout */}
          <Button
            onClick={handleLogout}
            variant="outline"
            className="w-full"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Logout
          </Button>
        </div>
      </div>
    </div>
  );
}

