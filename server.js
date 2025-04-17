const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
require("dotenv").config();

const app = express();
app.use(cors());
app.use(express.json());

const PORT = 5000;

//Connect to MongoDB Atlas
mongoose
  .connect(process.env.MONGO_URI, {
    useNewUrlParser: true,
    useUnifiedTopology: true,
  })
  .then(() => console.log("Connected to MongoDB Atlas"))
  .catch((err) => console.error("MongoDB Connection Error:", err));

// Define Schema & Model (Fixing Issue #1)
const userSchema = new mongoose.Schema({
  Month: String,
  Season: String,
  Budget: String,
  Temperature: Number,
  Weather: String,
  Activity_Preference: String,
  Group_Size: Number,
  Suggested_Place: String,
});

const User = mongoose.model("User", userSchema, "places"); // Ensuring it uses `places` collection

// API to fetch user travel data from `places` collection
app.get("/getUserData", async (req, res) => {
  try {
    const users = await User.find(); //Now using Mongoose instead of raw MongoDB
    res.json({ data: users });
  } catch (error) {
    console.error("Error fetching data:", error);
    res.status(500).json({ error: "Failed to fetch user data" });
  }
});

//  API to add user travel data
app.post("/addUserData", async (req, res) => {
  try {
    const newUser = new User(req.body);
    await newUser.save();
    res.status(201).json({ message: " User data added successfully!" });
  } catch (error) {
    console.error("Error adding user data:", error);
    res.status(500).json({ error: "Failed to add user data" });
  }
});

//  Start Express server
app.listen(PORT, () => console.log(` Server running on port ${PORT}`));
