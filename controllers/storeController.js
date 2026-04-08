import Store from "../models/Store.js";
import Category from "../models/Category.js";

export const createStore = async (req, res) => {
    try {
        const { name, image, categoryName } = req.body;

        // find category by name
        const category = await Category.findOne({ name: categoryName });

        if (!category) {
            return res.status(404).json({ message: "Category not found" });
        }

        const store = await Store.create({
            name,
            image,
            categoryId: category._id   // 🔥 updated
        });

        res.json(store);
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
};

export const getStoresByCategory = async (req, res) => {
    try {
        const { categoryId } = req.params;

        const stores = await Store.find({ categoryId }); // 🔥 updated

        res.json(stores);
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
};