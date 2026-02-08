# Fix: GitHub Desktop shows "Untracked: AIG-RLIC-REFINE-DEMO/" because
# the PARENT folder (Cursor) has a .git. This script removes the parent .git
# so that only AIG-RLIC-REFINE-DEMO is a repo.

$parent = "C:\Users\user\Desktop\Cursor"
$parentGit = Join-Path $parent ".git"
$projectGit = Join-Path $parent "AIG-RLIC-REFINE-DEMO\.git"

if (Test-Path $parentGit) {
    Write-Host "Removing parent .git from Cursor (so GitHub Desktop uses AIG-RLIC-REFINE-DEMO only)..."
    Remove-Item -Path $parentGit -Recurse -Force
    Write-Host "Done. Parent folder is no longer a Git repo."
} else {
    Write-Host "No .git found in parent (Cursor). Parent is already not a repo."
}

if (Test-Path $projectGit) {
    Write-Host "AIG-RLIC-REFINE-DEMO has .git - OK."
} else {
    Write-Host "WARNING: AIG-RLIC-REFINE-DEMO\.git not found. Run: cd AIG-RLIC-REFINE-DEMO; git init"
}

Write-Host ""
Write-Host "Next steps:"
Write-Host "1. In GitHub Desktop: File -> Remove (remove the current repo)."
Write-Host "2. File -> Add local repository -> Choose: $parent\AIG-RLIC-REFINE-DEMO"
Write-Host "3. You should see 1 commit and no untracked AIG-RLIC-REFINE-DEMO folder."
