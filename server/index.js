const express = require('express');
const WebSocket = require('ws');
const http = require('http');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const fs = require('fs');
const path = require('path');

// Initialize express app
const app = express();
const port = process.env.PORT || 8080;

// Security and utility middleware
app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(morgan('combined'));

// Create HTTP server
const server = http.createServer(app);

// Create WebSocket server
const wss = new WebSocket.Server({ server });

// Store connected clients
const clients = new Set();

// WebSocket connection handler
wss.on('connection', (ws) => {
  console.log('Client connected');
  clients.add(ws);
  
  // Send initial connection message
  ws.send(JSON.stringify({
    type: 'connection',
    message: 'Connected to MCP Server',
    timestamp: new Date().toISOString()
  }));
  
  // Handle incoming messages
  ws.on('message', (message) => {
    try {
      const parsedMessage = JSON.parse(message);
      console.log('Received message:', parsedMessage);
      
      // Handle different message types
      switch(parsedMessage.type) {
        case 'ping':
          ws.send(JSON.stringify({
            type: 'pong',
            timestamp: new Date().toISOString()
          }));
          break;
          
        case 'broadcast':
          // Broadcast to all clients
          broadcastMessage(parsedMessage.data);
          break;
          
        default:
          console.log('Unknown message type:', parsedMessage.type);
      }
    } catch (error) {
      console.error('Error processing message:', error);
    }
  });
  
  // Handle disconnection
  ws.on('close', () => {
    console.log('Client disconnected');
    clients.delete(ws);
  });
});

// Broadcast function for sending to all clients
function broadcastMessage(data) {
  const message = JSON.stringify({
    type: 'broadcast',
    data: data,
    timestamp: new Date().toISOString()
  });
  
  clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(message);
    }
  });
}

// REST API Routes
app.get('/status', (req, res) => {
  res.json({
    status: 'operational',
    clients: clients.size,
    uptime: process.uptime(),
    timestamp: new Date().toISOString()
  });
});

// Update endpoint (protected)
app.post('/update', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  
  // In production, implement proper authentication here
  const token = authHeader.split(' ')[1];
  
  // Simple validation for demo purposes
  if (token !== 'your-api-key') {
    return res.status(403).json({ error: 'Forbidden' });
  }
  
  console.log('Update request received');
  
  // Notify all clients about upcoming update
  broadcastMessage({
    type: 'system',
    message: 'Server update in progress'
  });
  
  res.json({ success: true, message: 'Update initiated' });
  
  // In a real scenario, you would trigger your update process here
  // For example: exec('npm run update', ...)
});

// Start the server
server.listen(port, () => {
  console.log(`MCP Server running on port ${port}`);
});