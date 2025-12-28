# Git & GitHub Setup for Collaboration

## Quick Answer: No, Cursor doesn't auto-save to GitHub
Cursor is a local code editor. You need to set up version control (Git) and push to GitHub for collaboration.

## Option 1: Git + GitHub (Recommended for Code)

### Benefits:
- ✅ Version history (see all changes)
- ✅ Conflict resolution
- ✅ Professional standard
- ✅ Free for public/private repos
- ✅ Works with any editor

### Setup Steps:

#### 1. Create GitHub Account (if you don't have one)
- Go to https://github.com
- Sign up for free account

#### 2. Create a New Repository on GitHub
- Click "New repository"
- Name it (e.g., "dmv-ocr-validator")
- Choose Private or Public
- **Don't** initialize with README (we already have files)
- Click "Create repository"

#### 3. Initialize Git in Your Project (Run these commands)

```bash
cd /Users/octane.hinojosa/WEB

# Initialize Git
git init

# Add all files
git add web.html backend_driverlic.py requirements.txt README.md start_server.* .gitignore

# Create first commit
git commit -m "Initial commit - DMVREAL"

# Add GitHub repository (replace YOUR_USERNAME and REPO_NAME)
git remote add origin https://github.com/KCD1111/DMVREAL.git

# Push to GitHub
git branch -M main
git push -u origin main
```

#### 4. Your Partner's Setup

Your partner should run:

```bash
# Clone the repository
git remote add origin https://github.com/KCD1111/DMVREAL.git
cd REPO_NAME

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Daily Workflow:

**When you make changes:**
```bash
# See what changed
git status

# Add changed files
git add .

# Commit with message
git commit -m "Description of changes"

# Push to GitHub
git push
```

**When your partner makes changes:**
```bash
# Get latest changes
git pull
```

**If both edit same file:**
- Git will help you merge changes
- You'll see conflict markers: `<<<<<<<`, `=======`, `>>>>>>>`
- Edit to resolve, then commit

---

## Option 2: Real-Time Collaboration Tools

### VS Code Live Share (Works with Cursor)
1. Install "Live Share" extension in Cursor
2. Click "Share" button
3. Send link to partner
4. Partner can edit in real-time

### Google Drive / Dropbox (Simple but Limited)
- Put project folder in shared Drive/Dropbox folder
- ⚠️ **Warning**: Can cause conflicts if both edit simultaneously
- ⚠️ Not ideal for code projects

### GitHub Codespaces (Cloud IDE)
- Edit code directly in browser
- Real-time collaboration
- Requires GitHub account

---

## Option 3: Hybrid Approach

Use Git for code + Live Share for real-time pair programming:
- Git: For version control and async collaboration
- Live Share: For real-time coding sessions

---

## Recommended Setup

**For your project, I recommend:**
1. Set up Git + GitHub (Option 1)
2. Both partners clone the repo
3. Use `git pull` before starting work
4. Use `git push` after making changes
5. Use Live Share extension for real-time sessions

---

## Quick Commands Reference

```bash
# Check status
git status

# See changes
git diff

# Add all changes
git add .

# Commit
git commit -m "Your message here"

# Push to GitHub
git push

# Get partner's changes
git pull

# Create new branch (for features)
git checkout -b feature-name

# Switch branches
git checkout main
```

---

## Need Help?

If you want me to help set up Git right now, I can:
1. Initialize the repository
2. Create the initial commit
3. Help you connect to GitHub

Just let me know!

