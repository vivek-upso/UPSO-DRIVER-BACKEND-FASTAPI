import mongoose from "mongoose";

const productSchema = new mongoose.Schema(
    {
        productName: {
            type: String,
            required: true
        },

        productCode: {
            type: String
        },

        brandName: {
            type: String
        },

        upcNumber: {
            type: String
        },

        mainCategory: {
            type: String
        },

        subCategory: {
            type: String
        },

        price: {
            type: Number
        },

        description: {
            type: String
        },

        unitCat: {
            type: String
        },

        images: [
            {
                type: String
            }
        ],

        // 🔥 IMPORTANT (for Store → Product navigation)
        store: {
            type: mongoose.Schema.Types.ObjectId,
            ref: "Store",
            required: true
        },

        // 🔥 Optional but useful (matches your frontend)
        quantity: {
            type: Number,
            default: 0
        },

        revenue: {
            type: Number,
            default: 0
        },

        monthlySale: {
            type: Number,
            default: 0
        }

    },
    { timestamps: true }
);

export default mongoose.model("Product", productSchema);