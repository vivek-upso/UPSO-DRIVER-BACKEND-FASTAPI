import OTP from "../models/otpModel.js";
import twilio from "twilio";

// 🔢 Generate OTP
const generateOTP = () => {
    return "123456"; // 🛠️ Dummy OTP for testing
};

// 📩 SEND OTP
export const sendOTP = async (req, res) => {
    try {
        const { mobile, role } = req.body;

        if (!mobile || !role) {
            return res.status(400).json({ message: "Mobile & role required" });
        }

        const otp = generateOTP();

        const expiryMinutes = Number(process.env.OTP_EXPIRY) || 5;
        const expiry = new Date(Date.now() + expiryMinutes * 60000);

        // ✅ Save to DB
        const record = await OTP.findOneAndUpdate(
            { mobile, role },
            { otp, expiresAt: expiry, verified: false },
            { upsert: true, returnDocument: 'after' } // ✅ FIXED: use returnDocument: 'after'
        );

        console.log(`OTP for ${mobile}: ${otp}`);

        // 🛡️ Twilio Config Check (Bypassed for Dummy OTP)
        /*
        const accountSid = process.env.TWILIO_ACCOUNT_SID || process.env.TWILIO_SID;
        const authToken = process.env.TWILIO_AUTH_TOKEN;

        if (!accountSid || !authToken) {
            return res.status(500).json({ error: "Twilio Configuration Error: Account SID or Auth Token is missing in .env file." });
        }
        
        if (!accountSid.startsWith("AC")) {
            return res.status(500).json({ error: `Twilio Error: Your Account SID '${accountSid}' is invalid. It MUST start with 'AC'. Please check your Twilio Dashboard and update .env` });
        }

        const client = twilio(accountSid, authToken);
        */

        // 📲 Send SMS (Commented out for Dummy OTP)
        /*
        const message = await client.messages.create({
            body: `Your OTP is ${otp}`,
            from: process.env.TWILIO_FROM, 
            to: mobile.startsWith("+") ? mobile : `+91${mobile}`, 
        });
        console.log("Twilio SID:", message.sid);
        */

        console.log(`[DUMMY MODE] OTP for ${mobile}: ${otp}`);

        res.json({
            success: true,
            message: "OTP sent successfully",
            data: record,
        });

    } catch (err) {
        console.error("Error:", err.message);
        res.status(500).json({ error: err.message });
    }
};

// ✅ VERIFY OTP
export const verifyOTP = async (req, res) => {
    try {
        const { mobile, otp, role } = req.body;

        if (!mobile || !otp || !role) {
            return res.status(400).json({
                message: "Mobile, OTP & role required",
            });
        }

        const record = await OTP.findOne({ mobile, role });

        if (!record) {
            return res.status(400).json({ message: "No OTP found" });
        }

        // ✅ Allow '123456' as a universal dummy OTP bypass
        if (record.otp !== otp && otp !== "123456") {
            return res.status(400).json({ message: "Invalid OTP" });
        }

        if (record.expiresAt < new Date()) {
            return res.status(400).json({ message: "OTP expired" });
        }

        record.verified = true;
        await record.save();

        res.json({
            success: true,
            message: "OTP verified successfully",
        });
    } catch (err) {
        console.error("Verify Error:", err.message);
        res.status(500).json({ error: err.message });
    }
};