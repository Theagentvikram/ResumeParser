const express = require('express');
const path = require('path');
const { createServer } = require('@vercel/node');

const app = express();

// Serve static files from the dist directory
app.use(express.static(path.join(__dirname, '../dist')));

// Fallback to index.html for SPA routing
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../dist', 'index.html'));
});

module.exports = app;
