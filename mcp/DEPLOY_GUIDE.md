# Step-by-Step Guide: Deploy MCP Server to Render.com

## What You'll Get
A permanent HTTPS URL like: `https://your-app-name.onrender.com`

---

## Step 1: Create a Render Account

1. Go to **[render.com](https://render.com)**
2. Click **"Get Started for Free"**
3. Sign up with GitHub, GitLab, or email
4. Verify your email if needed

---

## Step 2: Push Your Code to GitHub (if not already)

### Option A: If you don't have this code on GitHub yet

1. Go to **[github.com](https://github.com)** and sign in
2. Click the **"+"** button (top right) → **"New repository"**
3. Name it something like `mcp-convex-bridge`
4. Leave it **Public** or **Private** (your choice)
5. Click **"Create repository"**

6. In your terminal (in the `mcp` folder):

```powershell
# Initialize git (if not already done)
git init

# Add all files
git add .

# Make first commit
git commit -m "Initial MCP server"

# Connect to GitHub (replace with YOUR GitHub username and repo name)
git remote add origin https://github.com/YOUR-USERNAME/mcp-convex-bridge.git

# Push code
git branch -M main
git push -u origin main
```

### Option B: If code is already on GitHub
Skip to Step 3.

---

## Step 3: Create a New Web Service on Render

1. Log in to **[dashboard.render.com](https://dashboard.render.com)**
2. Click the **"New +"** button (top right)
3. Select **"Web Service"**

---

## Step 4: Connect Your Repository

1. Click **"Connect GitHub"** or **"Connect GitLab"**
2. **Authorize Render** to access your repositories
3. Find and click **"Connect"** next to your `mcp-convex-bridge` repository

---

## Step 5: Configure Your Service

Fill in these fields:

### Basic Settings
- **Name:** `mcp-convex-bridge` (or any name you want)
  - This becomes your URL: `https://mcp-convex-bridge.onrender.com`
- **Region:** Choose closest to you (e.g., Oregon, Frankfurt)
- **Branch:** `main`
- **Root Directory:** Leave blank OR type `mcp` if deploying from subfolder

### Build Settings
- **Runtime:** Select **Node**
- **Build Command:** 
  ```
  npm install && npm run build
  ```
- **Start Command:** 
  ```
  npm start
  ```

### Instance Type
- Select **"Free"** (starts automatically, may sleep after inactivity)
  - OR **"Starter"** ($7/month, always on, better performance)

---

## Step 6: Add Environment Variables

Scroll down to **"Environment Variables"** section.

Click **"Add Environment Variable"** for each of these:

| Key | Value |
|-----|-------|
| `CONVEX_URL` | Your Convex URL (e.g., `https://vivid-echidna-618.convex.cloud`) |
| `AUTH_TOKEN` | Make up a secret token (e.g., `super-secret-token-12345`) |
| `NODE_ENV` | `production` |

**DO NOT set PORT** - Render sets this automatically.

---

## Step 7: Deploy

1. Scroll to bottom
2. Click **"Create Web Service"**
3. Wait 2-5 minutes while Render:
   - Clones your code
   - Installs dependencies
   - Builds TypeScript
   - Starts the server

Watch the **Logs** section - you'll see build progress.

---

## Step 8: Check If It's Working

Once you see **"Your service is live"**:

1. Copy your service URL: `https://your-app-name.onrender.com`
2. In a browser, visit:
   ```
   https://your-app-name.onrender.com/health
   ```
3. You should see JSON like:
   ```json
   {
     "status": "healthy",
     "timestamp": "2026-04-19...",
     "clients": 0,
     "version": "1.0.0"
   }
   ```

---

## Step 9: Get Your MCP URL for Claude

Your MCP server URL is:

```
https://your-app-name.onrender.com/sse
```

**Example:** If your app is named `mcp-convex-bridge`:
```
https://mcp-convex-bridge.onrender.com/sse
```

**Save this URL** - you'll use it in Claude.

---

## Step 10: Add to Claude

### For Claude.ai Web:

1. Go to **claude.ai**
2. Click your profile (bottom left) → **Settings**
3. Go to **"Connectors"** or **"Custom Connectors"**
4. Click **"Add Connector"** or **"+"**
5. Enter:
   - **Name:** `Convex Products`
   - **URL:** `https://your-app-name.onrender.com/sse`
   - **Authorization:** Select type and paste your `AUTH_TOKEN`

### For Claude Desktop:

Edit config file at:
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Add:
```json
{
  "mcpServers": {
    "convex-products": {
      "url": "https://your-app-name.onrender.com/sse",
      "authorization_token": "YOUR_AUTH_TOKEN_HERE"
    }
  }
}
```

**Restart Claude Desktop completely** after saving.

---

## Troubleshooting

### "Service failed to start"
- Check **Logs** in Render dashboard
- Common issues:
  - Missing environment variables
  - Wrong build/start commands
  - TypeScript errors

### "Couldn't reach MCP server" in Claude
- Verify `/health` endpoint works in browser
- Check `AUTH_TOKEN` matches in Render and Claude
- Wait 1-2 minutes after deployment

### Free tier sleeps after inactivity
- First request after sleep takes 30-60 seconds
- Upgrade to **Starter** ($7/month) for always-on

---

## Your URLs Summary

After deployment, you'll have:

- **Health Check:** `https://your-app-name.onrender.com/health`
- **MCP Stream:** `https://your-app-name.onrender.com/sse`
- **Messages:** `https://your-app-name.onrender.com/messages`

---

## Need to Redeploy?

Any time you push code to GitHub:
1. `git add .`
2. `git commit -m "Update"`
3. `git push`

Render **automatically** rebuilds and redeploys.

---

## Cost

- **Free tier:** $0/month (sleeps after 15 min inactivity)
- **Starter:** $7/month (always on, no sleep)

Free tier is fine for testing!
