import mongoose from "mongoose";

const otpSchema = new mongoose.Schema({
    mobile: {
        type: String,
        required: true,
    },
    role: {
        type: String,
        enum: ["admin", "user", "vendor", "driver"],
        required: true,
    },
    otp: {
        type: String,
        required: true,
    },
    expiresAt: {
        type: Date,
        required: true,
    },
    verified: {
        type: Boolean,
        default: false,
    },
});

export default mongoose.model("OTP", otpSchema);