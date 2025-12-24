# Connect to DMVREAL Repository - Run These Commands

## ✅ Your Repository: DMVREAL

Since you've already created the repository on GitHub, just run these commands:

## Step 1: Add GitHub Remote

Replace `YOUR_USERNAME` with your actual GitHub username:

```bash
cd /Users/octane.hinojosa/WEB
git remote add origin https://github.com/YOUR_USERNAME/DMVREAL.git
```

**Example:** If your username is `octanehinojosa`:
```bash
git remote add origin https://github.com/octanehinojosa/DMVREAL.git
```

## Step 2: Set Branch to Main

```bash
git branch -M main
```

## Step 3: Push Your Code

```bash
git push -u origin main
```

## That's It! 🎉

Your code will be uploaded to GitHub. Your partner can then clone it with:

```bash
git clone https://github.com/YOUR_USERNAME/DMVREAL.git
```

## Troubleshooting

### "remote origin already exists"
If you get this error, remove the old remote first:
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/DMVREAL.git
```

### "Authentication failed"
GitHub requires a Personal Access Token instead of password:
1. Go to: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. Select scopes: `repo` (full control)
4. Copy the token
5. Use the token as your password when pushing

### "Repository not found"
- Make sure the repository name is exactly `DMVREAL` (case-sensitive)
- Check your GitHub username is correct
- Make sure the repository exists on GitHub

