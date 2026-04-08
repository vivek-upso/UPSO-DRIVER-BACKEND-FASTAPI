import Category from "../models/Category.js";

export const createCategory = async (req, res) => {
    try {
        const category = await Category.create(req.body);
        res.json(category);
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
};

export const getCategories = async (req, res) => {
    const data = await Category.find();
    res.json(data);
};