# Connect Your Local Git to GitHub

## ✅ Step 1: Git is Already Set Up!

Your local Git repository is initialized and your first commit is created!

## Step 2: Create GitHub Repository

1. **Go to GitHub**: https://github.com
2. **Sign in** (or create account if needed)
3. **Click the "+" icon** (top right) → "New repository"
4. **Repository settings**:
   - **Name**: `DMVREAL` ✅ (you already created this!)
   - **Description**: "DMV Document OCR Validator with address extraction"
   - **Visibility**: 
     - ✅ **Private** (recommended - only you and your partner can see)
     - Or Public (anyone can see)
   - ⚠️ **DO NOT** check "Initialize with README" (we already have files)
   - ⚠️ **DO NOT** add .gitignore or license (we have them)
5. **Click "Create repository"**

## Step 3: Connect Local Git to GitHub

After creating the repository, connect it with these commands:

```bash
cd /Users/octane.hinojosa/WEB

# Add GitHub as remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/DMVREAL.git

# Rename branch to main (if needed)
git branch -M main

# Push your code to GitHub
git push -u origin main
```

**Example:**
If your GitHub username is `johndoe`:
```bash
git remote add origin https://github.com/johndoe/DMVREAL.git
git branch -M main
git push -u origin main
```

**Your Repository Name:** `DMVREAL`

## Step 4: Set Up Git User (Optional but Recommended)

To have better commit history, set your name and email:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

**Example:**
```bash
git config --global user.name "Octane Hinojosa"
git config --global user.email "octane@example.com"
```

## Step 5: Your Partner's Setup

Once you've pushed to GitHub, your partner should:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/DMVREAL.git
   cd DMVREAL
   ```

2. **Set up environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Start coding!**

## Daily Workflow

### When You Make Changes:

```bash
# 1. Check what changed
git status

# 2. Add your changes
git add .

# 3. Commit with a message
git commit -m "Added new feature X"

# 4. Push to GitHub
git push
```

### When Your Partner Makes Changes:

```bash
# Get the latest changes from GitHub
git pull
```

### If Both Edit Same File:

Git will help you merge. You'll see conflict markers:
```
<<<<<<< HEAD
Your changes
=======
Partner's changes
>>>>>>> branch-name
```

Edit to resolve, then:
```bash
git add .
git commit -m "Resolved merge conflict"
git push
```

## Quick Commands Cheat Sheet

```bash
# Status
git status                    # See what changed
git log --oneline            # See commit history

# Making changes
git add .                     # Add all changes
git add filename.py           # Add specific file
git commit -m "Message"      # Save changes
git push                     # Upload to GitHub

# Getting changes
git pull                     # Get partner's changes
git fetch                    # Check for changes (doesn't merge)

# Branches (for features)
git checkout -b feature-name # Create new branch
git checkout main            # Switch to main branch
git merge feature-name       # Merge feature into main
```

## Troubleshooting

### "Repository not found"
- Check the URL is correct
- Make sure you have access (if private repo, partner needs to be added as collaborator)

### "Authentication failed"
- GitHub now requires a Personal Access Token instead of password
- Go to: GitHub → Settings → Developer settings → Personal access tokens → Generate new token
- Use token as password when pushing

### "Updates were rejected"
- Someone else pushed changes
- Run `git pull` first, then `git push`

## Next: Set Up Live Share

Now that Git is set up, follow `LIVE_SHARE_SETUP.md` to enable real-time collaboration!

