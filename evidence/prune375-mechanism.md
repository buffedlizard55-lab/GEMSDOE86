# Mechanism card — PRUNE <=3.75 px, R0 parent

- **Hypothesis:** At fixed unit mass, removing R0 dots within 375 m of mapped traces and refilling with the recorded H19-5 traversal order modestly reduces near-trace false-positive mass.
- **Mechanism:** Remove the measured <=3.75 px catalogue collar, then replace those dots with the first eligible cells in the original deterministic FIFO-BFS H19-5 order, all farther than 3.75 px from the catalogue. The count remains 37,654 and no other ranking or physical layer changes.
- **Non-fault mimic / confounder:** New-fault truth may occur within 300 m of known traces; roads, pipelines, alluvial channels, and map generalization can mimic near-trace responses. The H19-5 traversal is spatially/content-blind and refilling may disrupt spacing.
- **Predicted live change:** -0.002 DTI (**MODEL**, pre-registered band -0.010..+0.006). Treat |delta| <0.01 as no evidence; 0.2778 for R0 is a **CLAIM**, not a receipt.
- **Falsifier:** A same-entity public-chunk receipt >= +0.010 versus R0 falsifies the predicted small-negative direction.
- **Report only:** catalogue hide/recover is **PROXY**; leakage canary and SGMC control are diagnostics, never gates or scores.
- **Sources:** [FIFO-BFS ranking recipe](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/94b027bed628422b7b39b485cb918a3fc15e5364/src/gems27/thinning.py); [organizer note on new faults near known traces](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516); [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf).
