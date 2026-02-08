# Pushing this project with GitHub Desktop

## Fix: "Untracked files: AIG-RLIC-REFINE-DEMO/"

That message means GitHub Desktop has the **parent folder** (Cursor) as the repo, not this folder.

### Do this first (then add the repo again)

1. **Run the fix script**  
   Double‑click **`FIX_AND_ADD_TO_GITHUB_DESKTOP.bat`** (it’s in this folder).  
   It removes the parent’s `.git` so only this folder is a repo, and shows `git status`.

2. **Remove the wrong repo from GitHub Desktop**  
   - In GitHub Desktop: **File → Remove** (or **Repository → Remove**).  
   - Remove the repository that’s currently listed (the one where you see “AIG-RLIC-REFINE-DEMO/” as untracked).  
   - Do **not** delete any files; this only removes the repo from GitHub Desktop’s list.

3. **Add this folder (not the parent)**  
   - **File → Add local repository…**  
   - Click **Choose…**  
   - Go to: `C:\Users\user\Desktop\Cursor`  
   - **Double‑click** `Cursor` to open it.  
   - **Single‑click** `AIG-RLIC-REFINE-DEMO` so it is selected (the name is highlighted).  
   - Click **Select Folder** / **OK**.  
   - The path must end with **`AIG-RLIC-REFINE-DEMO`**, not `Cursor`.  
   - Click **Add repository**.

4. **Check**  
   You should see 1 commit and **no** “Untracked: AIG-RLIC-REFINE-DEMO/”. Then use **Push origin** or **Publish repository**.

---

## If you still need to create the Git repo (one time)

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

Then do **Step 2** above (Remove wrong repo → Add this folder).

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
