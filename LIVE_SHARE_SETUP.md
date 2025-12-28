# VS Code Live Share Setup Guide

## What is Live Share?
Live Share lets you and your partner edit code together in real-time, directly in Cursor. It's like Google Docs for code!

## Setup Steps

### Step 1: Install Live Share Extension

1. **Open Cursor**
2. **Open Extensions**:
   - Press `Cmd+Shift+X` (Mac) or `Ctrl+Shift+X` (Windows/Linux)
   - Or click the Extensions icon in the sidebar

3. **Search for "Live Share"**:
   - Type "Live Share" in the search box
   - Look for "Live Share" by Microsoft (it has a blue icon)

4. **Install**:
   - Click "Install" on the Live Share extension
   - It may also prompt you to install "Live Share Audio" - you can skip that unless you want voice chat

5. **Reload Cursor**:
   - After installation, you may need to reload Cursor
   - Press `Cmd+R` (Mac) or `Ctrl+R` (Windows/Linux)

### Step 2: Sign In to Live Share

1. **Sign in with GitHub** (recommended):
   - Click the "Live Share" icon in the left sidebar (or press `Cmd+Shift+P` and type "Live Share")
   - Select "Sign in with GitHub"
   - Authorize in your browser
   - You'll be signed in automatically

2. **Alternative - Sign in with Microsoft**:
   - If you prefer, you can sign in with a Microsoft account

### Step 3: Start a Collaboration Session

**As the Host (Person sharing their screen):**

1. **Open your project folder** in Cursor:
   - File → Open Folder → Select `/Users/octane.hinojosa/WEB`

2. **Start sharing**:
   - Click the "Live Share" button in the bottom status bar
   - Or press `Cmd+Shift+P` and type "Live Share: Start Collaboration Session"
   - A link will be copied to your clipboard

3. **Share the link**:
   - Send the link to your partner via:
     - Email
     - Slack/Teams
     - Text message
     - Any messaging app

**As the Guest (Person joining):**

1. **Click the link** your partner sent you
2. **Choose how to open**:
   - If Cursor is installed: It will open automatically
   - If not: You can open in browser (limited features)

3. **You're in!** You can now:
   - See the same files
   - Edit code in real-time
   - See your partner's cursor
   - Chat in the sidebar

### Step 4: Collaborate!

**Features you can use:**

- **Real-time editing**: Both can type at the same time
- **See cursors**: See where your partner is editing
- **Follow mode**: Click "Follow" to see what your partner is doing
- **Chat**: Use the chat panel to communicate
- **Share terminal**: Host can share terminal access
- **Share server ports**: Share localhost servers (like your Flask app!)

## Tips for Best Experience

### 1. Use Git for Version Control
- Live Share is great for real-time collaboration
- But still use Git to save your work:
  ```bash
  git add .
  git commit -m "Worked on feature X with partner"
  git push
  ```

### 2. Communication
- Use the chat feature in Live Share
- Or use a separate voice/video call
- Agree on who edits what to avoid conflicts

### 3. Save Frequently
- Live Share syncs in real-time, but:
  - Save files regularly (`Cmd+S` / `Ctrl+S`)
  - Commit to Git after completing features

### 4. Share Servers
- If you're running the Flask server locally:
  - Host can share the port (5001)
  - Guest can access `http://localhost:5001` on their machine!

## Troubleshooting

### "Can't connect to Live Share"
- Make sure both people are signed in
- Check your internet connection
- Try restarting Cursor

### "Extension not found"
- Make sure you installed "Live Share" (not "Live Share Audio")
- Reload Cursor after installation

### "Link expired"
- Links expire after a while
- Host needs to generate a new link

### "Can't see changes"
- Make sure both are in the same folder
- Try refreshing the session

## Quick Reference

**Start sharing:**
- Click Live Share icon in status bar
- Or: `Cmd+Shift+P` → "Live Share: Start Collaboration Session"

**Join session:**
- Click the link your partner sent

**Stop sharing:**
- Click "End Collaboration Session" in Live Share panel

**Share terminal:**
- Right-click terminal → "Share Terminal"

**Share server:**
- Live Share automatically detects localhost servers
- Guest can access them on their machine!

## Next Steps

1. ✅ Install Live Share extension (Step 1)
2. ✅ Sign in (Step 2)
3. ✅ Try starting a session with your partner
4. ✅ Practice editing together
5. ✅ Use Git to save your collaborative work

Enjoy real-time collaboration! 🚀

