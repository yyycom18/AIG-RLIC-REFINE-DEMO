# Pushing this project with GitHub Desktop

## If the push fails or the repo is not set up yet

### Step 1: Create the Git repo (one time)

1. Open **Command Prompt** or **PowerShell**.
2. Go to this folder:
   ```bat
   cd C:\Users\user\Desktop\Cursor\AIG-RLIC-REFINE-DEMO
   ```
3. Run:
   ```bat
   git init
   git add .
   git commit -m "Initial commit: AIG Investment Clock"
   ```

### Step 2: Add the repo in GitHub Desktop

1. Open **GitHub Desktop**.
2. **File → Add local repository…**
3. Click **Choose…** and select the folder:  
   `C:\Users\user\Desktop\Cursor\AIG-RLIC-REFINE-DEMO`
4. If it says "this directory does not appear to be a Git repository", go back to Step 1 and run `git init` and `git commit` in that folder.
5. After the repo is added, use **Repository → Repository settings…** and set the **Primary remote repository** to:
   ```text
   https://github.com/yyycom18/AIG-RLIC-REFINE-DEMO.git
   ```
   (Or create the repo on GitHub first, then set this URL.)

### Step 3: Publish or push

- If the GitHub repo **does not exist yet**: click **Publish repository**, choose the account (yyycom18), name it `AIG-RLIC-REFINE-DEMO`, then **Publish**.
- If the repo **already exists**: click **Push origin** (or **Fetch origin** then **Push origin**).

---

## If push still fails

- **"Authentication failed"**  
  In GitHub Desktop: **File → Options → Accounts** and sign in again, or re-add the GitHub account.

- **"Repository not found" or "remote not found"**  
  Create the repo on GitHub: https://github.com/new → name: `AIG-RLIC-REFINE-DEMO` → Create.  
  Then in GitHub Desktop: **Repository → Repository settings** → set the remote URL to  
  `https://github.com/yyycom18/AIG-RLIC-REFINE-DEMO.git`.

- **"File over 100 MB" or "large files"**  
  This project’s `.gitignore` is set so that `data/*.csv`, `data/*.json`, and `outputs/*.json` are not committed. Do not force-add those files. If you already committed them, remove them from the last commit or use `git filter-branch` / BFG (search for “GitHub remove large file from history”).

- **"Failed to push" with no details**  
  In GitHub Desktop, open **Repository → Open in Command Prompt** and run:
  ```bat
  git push -u origin main
  ```
  If the default branch is `master`, use:
  ```bat
  git branch -M main
  git push -u origin main
  ```
  Any error message shown there will explain the problem.
