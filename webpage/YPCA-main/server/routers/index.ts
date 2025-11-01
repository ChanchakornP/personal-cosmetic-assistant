import { router } from "../trpc";
import { authRouter } from "./auth";
import { productRouter } from "./product";
import { ingredientConflictRouter } from "./ingredientConflict";

export const appRouter = router({
    auth: authRouter,
    product: productRouter,
    ingredientConflict: ingredientConflictRouter,
});

export type AppRouter = typeof appRouter;

