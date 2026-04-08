import express from "express";
import { createStore, getStoresByCategory } from "../controllers/storeController.js";

const router = express.Router();

router.post("/", createStore);

// category → stores
router.get("/category/:categoryId", getStoresByCategory);

export default router;