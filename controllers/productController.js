import Product from "../models/Product.js";

// ➕ Create Product

import Store from "../models/Store.js";

export const createProduct = async (req, res) => {
    try {
        const {
            productName,
            price,
            brandName,
            subCategory,
            mainCategory,
            quantity,
            images,
            storeName,   // Accept storeName from client
        } = req.body;

        // Find store by name
        const store = await Store.findOne({ name: storeName });

        if (!store) {
            return res.status(404).json({ message: "Store not found" });
        }

        // Create product with store's ObjectId
        const product = await Product.create({
            productName,
            price,
            brandName,
            subCategory,
            mainCategory,
            quantity,
            images,
            store: store._id,  // Use the found store ID here
        });

        res.status(201).json(product);
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
};
// 📦 Get All Products
export const getAllProducts = async (req, res) => {
    try {
        const products = await Product.find().populate("store");
        res.json(products);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

// 🔥 Get Products by Store (MAIN REQUIREMENT)
export const getProductsByStore = async (req, res) => {
    try {
        const { storeId } = req.params;

        const products = await Product.find({ store: storeId });

        res.json(products);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

// 🔍 Get Single Product
export const getSingleProduct = async (req, res) => {
    try {
        const product = await Product.findById(req.params.id).populate("store");

        if (!product) {
            return res.status(404).json({ message: "Product not found" });
        }

        res.json(product);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

// ✏️ Update Product
export const updateProduct = async (req, res) => {
    try {
        const updated = await Product.findByIdAndUpdate(
            req.params.id,
            req.body,
            { new: true }
        );

        res.json(updated);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

// ❌ Delete Product
export const deleteProduct = async (req, res) => {
    try {
        await Product.findByIdAndDelete(req.params.id);
        res.json({ message: "Product deleted" });
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};