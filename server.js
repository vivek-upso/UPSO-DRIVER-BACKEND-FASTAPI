// const express = require("express");
// const mongoose = require("mongoose");
// const dotenv = require("dotenv");
// const cors = require("cors");
// // const swaggerUi = require("swagger-ui-express");
// // const swaggerDocument = require("./swagger.json");
// const dns = require("dns");
// dns.setServers(["1.1.1.1", "8.8.8.8"]);

// dotenv.config();

// const app = express();
// app.use(cors());
// app.use(express.json());

// // // Routes

// const otpRoutes = require("./routes/otpRoutes");
// import categoryRoutes from "./routes/categoryRoutes.js";
// import storeRoutes from "./routes/storeRoutes.js";
// import productRoutes from "./routes/productRoutes.js";


// app.use("/api/otp", otpRoutes);
// app.use("/api/categories", categoryRoutes);
// app.use("/api/stores", storeRoutes);
// app.use("/api/products", productRoutes);


// // DB connect
// mongoose
//     .connect(process.env.MONGO_URI)
//     .then(() => console.log("MongoDB Connected"))
//     .catch((err) => console.log(err));

// app.get("/", (req, res) => res.send("API Running 🚀"));

// const PORT = process.env.PORT || 5000;
// app.listen(PORT, () => console.log(`Server running on port ${PORT}`));

import express from "express";
import mongoose from "mongoose";
import dotenv from "dotenv";
import cors from "cors";
import dns from "dns";

import otpRoutes from "./routes/otpRoutes.js";
import categoryRoutes from "./routes/categoryRoutes.js";
import storeRoutes from "./routes/storeRoutes.js";
import productRoutes from "./routes/productRoutes.js";

dotenv.config();

const app = express();

app.use(cors());
app.use(express.json());
dns.setServers(["8.8.8.8", "8.8.4.4"]);
// Routes
app.use("/api/otp", otpRoutes);
app.use("/api/categories", categoryRoutes);
app.use("/api/stores", storeRoutes);
app.use("/api/products", productRoutes);

// DB connect
mongoose
    .connect(process.env.MONGO_URI)
    .then(() => console.log("MongoDB Connected"))
    .catch((err) => console.log(err));

app.get("/", (req, res) => res.send("API Running 🚀"));

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));