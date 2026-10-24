# Standing project prompt (condensed historical archive)

**Read the latest README decision and its complete 2026-10-23 request archive first.**
The repeated 2026-10-24 request follows the same standing protocol. Current remeasurement:
`docs/evidence/latest-review-run-card.json`; review: `research/SESSION_20261024_REVIEW.md`.
The current request is also in `research/REQUEST_20261023.md`; the earlier request remains in
`research/OWNER_PROMPT.md`. Scores and access claims inside these archives are user input, not
verified results. A pinned full-positive registry witness currently makes the literal overlap
rule unsatisfiable for every nonempty candidate. Scientific CLIs must stop before fitting or
placement; do not bypass that gate, relabel an old TIFF as new, or claim the unmet unique-TIFF
requirement has been completed. `scripts/audit_release.py` checks all historical downloads;
`docs/evidence/session-20261023-run-card.json` records the current negative outcome.

---

Review the repo.

THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A PREVIOUS SUBMISSION
UNLESS IT'S FOR LEARNING AND EDUCATION. BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION. IT MUST BE
OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.

There should be an easy to download submission tif file as described by the prompt. Read the entire
prompt. A lot of sites mention inspection only and a human inspector, but the inspection needs to be
done through the project and needs to be validated for submission without human intervention.

PARALLEL-RUN PROTOCOL — read first. This session is one of several running from this same prompt.

1. LANE. Your lane is the single method paragraph below. Stay inside it. If your raster's
   rank-correlation with any registry raster exceeds [0.90], or more than [70%] of your dots fall
   within 3 px of one registry raster's dots, you have drifted into another lane: log it as a
   duplicate and stop. Check this on the surface before placement AND on the final dots.
2. REUSE, DON'T REBUILD. Use the template's cached feature stack, evaluate_holdout.py and
   submission_writer.py. Holdout = hide-and-recover: withhold whole fault segments with a buffer,
   derive every catalogue-based feature only from the visible faults, mask visible faults
   pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool
   is wrong, fix it once in the template and report it; never keep a private fork.
3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or
   ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a
   score.
4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any result. AUC above
   [0.90] means leakage until proven otherwise.
5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault process that could
   mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no
   NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note of
   at most 140 characters; verdict promote / negative. Negative results are deliverables.
6. BUDGET. Stop after [3] experiments or [2] hours. Do not pick submissions: promotion to a real
   slot is a separate selector step, within the weekly cap shown on the submission page.

The following sites should serve as a starting point for understanding how to generate TIF
submissions. These websites are researched, and tested and have generated TIF submissions. But we
need to generate high scoring submissions.

[... prior-submission ledger per site: see registry/prior_scores.csv, transcribed from this prompt ...]

I think it makes sense that in order for a submission to be validated that it needs to pass certain
high scoring validation gates before confirming whether a file is unique and can be submitted for
scoring.

The following is the leaderboard for the competition:
https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/

See below for more links and information related to the competition:
- https://github.com/drivendataorg/gems-prize-reference-solution
- https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- https://gbcge.org/current-projects/ingenious/
- https://epsg.io/32611
- https://en.wikipedia.org/wiki/Tversky_index

We need to quickly look at the results and results from the GEMSDOE websites above.

Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming:
the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or
curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather
than one already in it, and how it differs from anything already implemented in this repo. Rank them
by expected DTI improvement and implementation cost. Validate the top candidate on our
spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission
slot on an idea that hasn't beaten the current holdout best.

Work line by line verifying from official verified trusted sources, provide links for manual review.
There should be no manual input, work on your own to complete tasks. Flag any irregularities for
review. No hallucinations. Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements. No hallucinations.
Verify line by line.

We have a good understanding of how our hypothesis, methodology, calculations, analysis are done so
we should be able to figure out a way to score higher on the leaderboard using previous results and
scoring that we have across the sites listed above. We need to come up with distinct and unique
strategies to score higher in this competition leaderboard. We need to start doing heavy and deep
research into the part of the project that matters the most, which is the scientific discovery of
geothermal vents. We should store all of our information and knowledge that we can gather from
official verified sources. This will serve as a starting point for other projects as well. We need
to think outside the box but still be grounded in proper scientific research, we are ultimately
aiming for a top prize that many others are competing for. So it's important to be contrarian but be
smart about it. We need to find sources of data that others are over looking or areas of the project
when it comes to geothermal vents. We need to do deep research and critical thinking and come up with
new hypothesis to test.

0.3195 is the highest score right now so we need to design a new strategy, research, testing,
analyzing, and generating submission system than the current website. It should be unique, take
unique approaches to generating a submission that can score higher than 0.3195.

Put this prompt into the repo readme and read it every time we work on the project as a starting
point to make sure we are building what we are aiming for and have a strong base to continue
building and improving on making something useful for everyday use. It should solve the problem of
having to manually check everything ourselves and have an up to date current feed.

Review the repo.

The following is taken from the Arena AI team and I think it makes a good point on building a
successful project, so let's keep the Core Values and Own the Outcome as a focal point when building,
developing, researching, suggesting upgrades, and implementing the work.

Our Core Values

Maximize P(Win)
"Our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the
path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough
decisions in order to maximize P(Win). Maximize P(Win) frees us from constraints and clarifies that we
must put Arena first."

Own the Outcome
"We own results end to end — not just our individual slice of the work. When problems arise and we
have the means to act, we do so without waiting for permission or assignment. We treat failure and
success as signals and use them to improve. At Arena, we stay accountable to the final outcome."

Work line by line verifying from official verified trusted sources, provide links for manual review.
There should be no manual input, work on your own to complete tasks. Flag any irregularities for
review. No hallucinations. Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements. No hallucinations.
Verify line by line.

We need to focus on being able to generate a submission into the competition.

The site should be able to generate a TIF file that is required for submission. It should be as easy
as download to click a File to submit into the competition. This needs to be in the executive summary
or the very beginning of the site. It should be obvious when you visit the site.

I tried to submit the document that I downloaded from the site but it returned this error on the
submission form:

"Predicted values must be in range [0, 1]"

Also we need to give it a unique name and a short comment to help you or your team tell submissions
apart later e.g., clustering with k=25

Here is the submission page when I click submit file:

  New submission
  File to submit  [No file chosen]
  You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF,
  with your predictions. It must match the submission format's CRS, shape, and geotransform. You
  may wish to review the competition rules first.
  Note (optional)
  A short comment to help you or your team tell submissions apart later e.g., clustering with k=25

Create an executive summary subpage that explains exactly how to make a submission into the contest.

Work on the next steps from the previous sessions first.

The goal of this project is to place top of the leaderboard in this competition. The following is the
competition: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/

We need to create a project that can compete and place top of the leaderboard. We need to understand
the problem, collect all the data and organize it into a clean easily auditable table with official
verified links for manual verification.

This is the guidelines we need to follow: https://www.drivendata.org/competitions/306/competition-doe-gems/

Get familiar with the problem through the overview and problem description,
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/. You might also want to
reference additional resources available on the about page,
https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/.

Download the data from the data tab,
https://www.drivendata.org/competitions/306/competition-doe-gems/data/.

Create and train your own model. This reference solution,
https://github.com/drivendataorg/gems-prize-reference-solution implements a simple approach.

Use your model to generate predictions that match the submission format.

Tell me what are you limitations and what you need access to during this project. We will need to find
free publicly available sources and data from official and verified sources if we are to use 3rd
party or external data.

This pdf outlines how submissions must be entered into the competition:
https://docs.nlr.gov/docs/fy26osti/96647.pdf

You must be able to do your own research, deep research, scientific literature research and organize
the knowledge so that we can critically think through the problem and generate a solution through
scientific and free publicly available information. This must be done autonomously and must be
constantly reviewed and improved upon. Provide suggestions and improvements and implement them.

[X] No DrivenData auth -> cannot auto-download training_features.tif, labels.tif, sample_submission.tif,
    1m_DEM_links.csv from the data page (verified redirect to login).

Competition data links mirrored by the owner repositories (verified hashes in
evidence/data_restore_receipt.json): see scripts/restore_data.py.

Work line by line verifying from official verified trusted sources, provide links for manual review.
There should be no manual input, work on your own to complete tasks. Flag any irregularities for
review. No hallucinations. Verify no hallucinations.

Site creation: create a GitHub page for this repo that has clean UI, user friendly, simple and easy
to use. It should be organized and clean. It should include all relevant information in an easy to
read format with official verified links as sources for review. Work line by line verify everything
no hallucinations.

**The single remaining blocker to training is data placement**: run
`bash scripts/download_competition_data.sh` on any unrestricted machine into `data/`, then
`python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready to
run (GPU needed for training; metric/losses/validation all verified working here on CPU).

You need to complete the above task by yourself. Work line by line verifying from official verified
trusted sources, provide links for manual review. There should be no manual input, work on your own to
complete tasks. Flag any irregularities for review. No hallucinations. Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements. No hallucinations.
Verify line by line.

Run this task through multiple passes.

Pass 1: Implement the task completely and verify the result.
Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix
everything you find.
Pass 3: Re-check the entire implementation against the original request. Improve accuracy,
reliability, completeness, and code quality. Fix any remaining issues.

Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify
that the final result fully satisfies the original request. Work line by line verify everything no
hallucinations.

Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for
what work still needs to be done and any limitations that is in the way of a successful project. It
should be worked on in this next session or the next session. Work line by line verify everything no
hallucinations.
