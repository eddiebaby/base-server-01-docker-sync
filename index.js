// Simple Express server to verify container works
const express = require("express");
const app = express();
const port = 3000;

// Log when starting up
console.log("MCP client starting up...");

// Basic endpoint
app.get("/", (req, res) => {
  console.log("Received request on root endpoint");
  res.send("MCP Client is running");
});

app.get("/status", (req, res) => {
  console.log("Received request on status endpoint");
  res.json({ status: "running", timestamp: new Date().toISOString() });
});

// Start server
app.listen(port, () => {
  console.log(`MCP Client running on port ${port}`);
});
