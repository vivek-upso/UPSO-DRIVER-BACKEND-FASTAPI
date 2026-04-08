import express from "express";
import {
    createProduct,
    getAllProducts,
    getProductsByStore,
    getSingleProduct,
    updateProduct,
    deleteProduct
} from "../controllers/productController.js";

const router = express.Router();

// ➕ Create
router.post("/", createProduct);

// 📦 Get all
router.get("/", getAllProducts);

// 🔥 Store → Products (IMPORTANT)
router.get("/store/:storeId", getProductsByStore);

// 🔍 Single product
router.get("/:id", getSingleProduct);

// ✏️ Update
router.put("/:id", updateProduct);

// ❌ Delete
router.delete("/:id", deleteProduct);

export default router;