import { router } from "../trpc";
import { authRouter } from "./auth";
import { productRouter } from "./product";
import { ingredientConflictRouter } from "./ingredientConflict";
import { skincareRoutineRouter } from "./skincareRoutine";

export const appRouter = router({
    auth: authRouter,
    product: productRouter,
    ingredientConflict: ingredientConflictRouter,
    skincareRoutine: skincareRoutineRouter,
});

export type AppRouter = typeof appRouter;

