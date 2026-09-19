# Kickoff prompt

Start a new Claude Code session **in this folder** (`C:\Users\tim\git\catamount-results`)
so `CLAUDE.md` loads and the session is attached to this repo, then paste the block
below. Delete this file once the work it describes is done.

---

```
Read CLAUDE.md and KICKOFF.md, then continue from "Next steps" in order. Work one
step at a time and show me what you see before moving on. Ask before any
force-push or anything that touches a repo other than this one.
```

---

## Where things stand

- The interface is built and verified in a browser against **invented sample data**:
  racer profiles, rivals, head-to-head, per-course pages, seasons, weather, and
  lap-distance-aware placings.
- **Nothing has been scraped from the real site yet.** The parser has never seen a
  real Webscorer page. Earlier sessions ran in a cloud sandbox that blocked
  webscorer.com; from this machine both webscorer.com and open-meteo.com respond.
- The pre-commit guard was fixed in the last commit: it used to swallow the exit
  code of a repo's own pre-commit hook, which would have silently disabled
  `detect-secrets` in other repos if installed globally. Failure now propagates
  (tested with a failing and a passing stand-in hook).
- The Strava idea was dropped entirely.

## Next steps

Verify in this order. Do not batch-fetch until each step checks out.

1. **Enable the guard:** `git config core.hooksPath .githooks`
2. **Discovery.** `python scrape.py discover`, then open `cache/organizer.html`
   and grep it for `raceid=`. If there are zero matches the listing is
   JS-rendered and discovery is dead: fall back to seeding known ids with
   `--ids`, or find a different index page. Also confirm `?pg=N` is really
   Webscorer's pagination parameter and not a guess.
3. **One race first.** Fetch exactly one race, check `score_table` picked the
   results grid and the header synonym map covers the real column names.
4. **Check lap counts survive. This matters most.** Grep a cached race page for
   `lap` (case-insensitive) and see where laps actually live. If `lap_count()`
   finds nothing, every row lands in one "?" division and the lap model silently
   collapses. After the scrape, confirm `lapCount` is populated on real rows.
   Also check whether Webscorer's printed place is overall or per-distance
   (the UI recomputes it per lap group regardless).
5. **Batch.** Fetch all races, then `python scrape.py weather`, then
   `python scrape.py build`. Expect Tim Burgher to appear with 3- and 4-lap
   starts, and not to appear in 2026.
6. **Replace the sample data.** A real `build` writes a bundle without the `sample`
   flag, which is what hides the "Sample data" banner. Confirm the banner is gone,
   then re-run the UI checks against the real bundle.
7. **Commit through the hook and push.** Scan the diff for anything you did not
   mean to publish before pushing; this repo is public.

## After the data is real

- **Deploy** (Cloudflare Pages, same pattern as `burghertime-landing`). Needs Tim:
  create Pages project `catamount-results` (direct upload, no Git connection); add
  repo secret `CLOUDFLARE_API_TOKEN` and repo variable `CLOUDFLARE_ACCOUNT_ID`;
  add custom domain `catamount.burghertime.com`. Do not add the secrets until the
  sample data is gone.
- **Landing page link.** Branch `add-catamount-link` in `burghertime-landing` has
  the card. Merge only once `catamount.burghertime.com` resolves, because pushing
  to that repo's `master` auto-deploys and the link would 404.
- **Optional:** install the email guard for every repo with
  `sh tools/protect-email.sh`. Tim's `family-mail-digest` and `someday` repos have
  their own `detect-secrets` pre-commit hooks; the chaining fix means they should
  keep running, but confirm by making a test commit in each before relying on it.
  Independently of any hook, GitHub → Settings → Emails → "Block command line
  pushes that expose my email" is the one layer that covers every machine.

## Separate task, different repo: finish the history rewrite

`burghertime-landing`'s original history is authored with a personal email
(private repo, so not exposed, but it would be if it ever went public). A clean
copy already exists on the remote as `master-clean`. **Do this from that repo's
folder, with Tim's go-ahead for the force-push:**

- Local `master` there has one **unpushed** commit, `019a195` (Dependabot config,
  already noreply-authored). `master-clean` does not contain it. Replay it first:
  `git checkout -B master-fixed origin/master-clean && git cherry-pick 019a195`
- Verify: `git log origin/master..master-fixed` shows the 6 rewritten commits plus
  the Dependabot one, and `git diff 019a195 master-fixed` is empty.
- Force-push with a lease on the exact old tip:
  `git push --force-with-lease=master:c1eca65199a68452601e1e44deec7254f95a787c origin master-fixed:master`
  (content is unchanged, so the Cloudflare redeploy is a no-op).
- Rebuild `add-catamount-link` on the new master by replaying `309249e`. That
  commit also added a copy of `.githooks/pre-commit` **with the old chaining bug**;
  replace it with the fixed version from this repo when replaying.
- Then delete the remote `master-clean` and old `add-catamount-link`.
- Any other clone of that repo diverges; re-clone or `git reset --hard origin/master`.
