exports.validateMobile = (req, res, next) => {
    const { mobile } = req.body;

    if (!mobile || mobile.length < 10) {
        return res.status(400).json({ message: "Invalid mobile number" });
    }

    next();
};