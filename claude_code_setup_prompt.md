# Claude Code — deploy The AI Brief to GitHub Pages

## Before you start (one time)
Make sure the GitHub CLI is installed and authenticated. In a terminal:

```
gh --version          # if "command not found": brew install gh
gh auth login         # choose GitHub.com → HTTPS → "Login with a web browser"
```

The browser login grants the `repo` and `workflow` scopes Claude Code needs to
push the workflow file and turn on Pages.

## Then: open Claude Code in this folder and paste the prompt below

```
cd ~/Desktop/CLAUDE/02_Personal-Business/ai_briefing_page/repo
claude
```

---

PROMPT TO PASTE INTO CLAUDE CODE:

I want to publish the files in this folder as a GitHub Pages site that
auto-refreshes daily. Please do all of this for me using git and the `gh` CLI,
showing me each command before you run it:

1. Initialize a git repo on branch `main`, add all files, and make an initial
   commit.
2. Create a NEW PUBLIC GitHub repo named `ai-brief` under my account and push to
   it. (The `.github/workflows/refresh.yml` file must be included.)
3. Enable GitHub Pages, deploying from the `main` branch, root folder `/`.
4. Set the repo's Actions workflow permissions to read AND write, so the daily
   job can commit the refreshed `index.html`.
5. Trigger the "Refresh AI Brief" workflow once now so the page builds
   immediately.
6. Print my live page URL (https://<my-username>.github.io/ai-brief/) and tell
   me when Pages is live.

If any `gh api` call needs my username, get it from `gh api user --jq .login`.
Stop and ask me if anything needs a permission or scope you don't have.

---

## Reference: the commands it will run
(For your awareness — Claude Code will adapt these as needed.)

```
git init -b main
git add .
git commit -m "Initial commit: The AI Brief"
gh repo create ai-brief --public --source=. --remote=origin --push

OWNER=$(gh api user --jq .login)
gh api -X POST "repos/$OWNER/ai-brief/pages" \
  --input - <<'JSON'
{ "source": { "branch": "main", "path": "/" } }
JSON

gh api -X PUT "repos/$OWNER/ai-brief/actions/permissions/workflow" \
  -F default_workflow_permissions=write

gh workflow run "Refresh AI Brief"
echo "https://$OWNER.github.io/ai-brief/"
```

Pages can take 1–2 minutes to go live the first time. After that, the page
rebuilds every day at noon Central via the scheduled workflow.
