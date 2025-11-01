import express from "express";
import { createExpressMiddleware } from "@trpc/server/adapters/express";
import { appRouter } from "./routers";
import { createContext } from "./context";

const app = express();
const PORT = process.env.PORT || 3001;

// CORS middleware
app.use((req, res, next) => {
    const origin = req.headers.origin;
    const allowedOrigins = process.env.ALLOWED_ORIGINS?.split(",") || ["http://localhost:5173", "http://localhost:3000"];

    if (origin && allowedOrigins.includes(origin)) {
        res.setHeader("Access-Control-Allow-Origin", origin);
    }
    res.setHeader("Access-Control-Allow-Credentials", "true");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

    if (req.method === "OPTIONS") {
        res.sendStatus(200);
        return;
    }
    next();
});

app.use(express.json());

// tRPC endpoint
app.use(
    "/api/trpc",
    createExpressMiddleware({
        router: appRouter,
        createContext: (opts) => createContext({ req: opts.req, res: opts.res }),
    })
);

// Health check
app.get("/health", (req, res) => {
    res.json({ ok: true, service: "PCA tRPC Server" });
});

app.listen(PORT, () => {
    console.log(`tRPC server running on port ${PORT}`);
});

