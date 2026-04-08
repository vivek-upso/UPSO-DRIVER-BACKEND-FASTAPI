import mongoose from "mongoose";

const storeSchema = new mongoose.Schema({
    name: {
        type: String,
        required: true
    },
    image: String,

    // 🔥 changed field name
    categoryId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: "Category",
        required: true
    }

}, { timestamps: true });

export default mongoose.model("Store", storeSchema);