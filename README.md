# The AI Brief — auto-refreshing daily page

A single dark-theme web page that lists the day's biggest AI developments,
filtered for the Big 4 / international-tax lens. It rebuilds itself every day
from Google News (no API key, no cost) and publishes to GitHub Pages, so you
can open the same link from any computer.

## What's in here

| File | What it does |
|---|---|
| `index.html` | The published page. The daily job overwrites this. |
| `template.html` | The page shell. `build.py` drops the story cards into it. |
| `build.py` | Pulls Google News RSS, tags + dedupes, writes `index.html`. Stdlib only. |
| `.github/workflows/refresh.yml` | Runs `build.py` daily at noon Central and commits the result. |

## One-time setup (about 10 minutes, all in the browser)

1. **Create the repo.** On github.com click **+ → New repository**. Name it
   `ai-brief`, set it **Public**, and create it. (Public is required for free
   GitHub Pages. Nothing sensitive lives here — there are no keys in the code.)

2. **Upload these files.** On the new repo page click **Add file → Upload files**,
   then drag in `index.html`, `template.html`, `build.py`, and `README.md`.
   Commit.

3. **Add the workflow file.** The uploader can't make folders, so click
   **Add file → Create new file** and type this exact name in the box:
   `.github/workflows/refresh.yml` — GitHub turns the slashes into folders.
   Paste the contents of the local `refresh.yml`, then commit.

4. **Allow the workflow to publish.** Go to **Settings → Actions → General →
   Workflow permissions**, choose **Read and write permissions**, and save.

5. **Turn on Pages.** Go to **Settings → Pages**. Under "Build and deployment"
   set **Source: Deploy from a branch**, **Branch: main / (root)**, save.
   After a minute your link appears at the top: `https://<you>.github.io/ai-brief/`.
   That's the link to bookmark on any device.

6. **Run it once now (optional).** Go to the **Actions** tab → **Refresh AI
   Brief** → **Run workflow**. This refreshes the page immediately instead of
   waiting for noon.

## Schedule

The page rebuilds daily at **17:00 UTC = noon in Houston (CDT)**. Cron uses UTC,
so when the US switches to standard time in November, edit the `cron:` line in
`refresh.yml` to `0 18 * * *` to keep it at noon.

Note: GitHub pauses scheduled workflows if a repo has no activity for 60 days.
The daily commit counts as activity, so this keeps itself alive.

## Editing the look

The design lives in `template.html`. Edit colors, fonts, or the masthead there,
commit, and the next run picks it up. To change which stories appear, edit the
`QUERIES` list near the top of `build.py`.

## Upgrading to Claude-curated summaries (later)

The free version uses news snippets. To get polished, filtered summaries written
each morning, the build step can call the Anthropic API instead — that needs an
API key saved as a GitHub secret. Ask Claude to wire this in when you're ready.
