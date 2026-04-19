# Render Deployment Guide

This MCP server is configured for Render.com deployment.

## Environment Variables Required on Render

Set these in your Render service dashboard:

- `CONVEX_URL` - Your Convex deployment URL
- `AUTH_TOKEN` - Secret token for authentication
- `NODE_ENV` - Set to `production`
- `PORT` - Leave blank (Render sets this automatically)

## Build & Start Commands

Render will automatically use:
- **Build Command:** `npm install && npm run build`
- **Start Command:** `npm start`
