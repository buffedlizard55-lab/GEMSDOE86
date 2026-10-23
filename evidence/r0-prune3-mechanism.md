# Mechanism card — h33-h33-2-b2-prune3-20261023-01d57649

- **Hypothesis:** At fixed mass, H19-5 cells beyond 300 m from the catalogue are more efficient than R0 cells in the 200–300 m annulus.
- **Mechanism:** Remove all 2,171 R0 dots at catalogue distance ≤3 px (5.7657% of R0) and refill the same number from the pinned H19-5 field at >3 px, using the [original deterministic FIFO-BFS order](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/94b027bed628422b7b39b485cb918a3fc15e5364/src/gems27/thinning.py). Count stays 37,654; the symmetric difference is 11.5313% of R0's count.
- **Non-fault mimic:** Roads, pipelines, alluvial channels and cartographic generalization can create fault-like responses beside mapped traces. The refill order is spatial/content-blind, not a new geological probability.
- **Predicted live change:** **−0.004 DTI (MODEL)**. The prior 2 px prune was beneficial, but [new-fault truth may occur within 300 m of known traces](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) and a dense fixed-count refill can add redundant false-positive mass.
- **Falsifier:** A comparable public-chunk receipt ≥+0.01 versus R0 falsifies the predicted direction. A change with absolute value <0.01 is no evidence.
- **Confounder:** Only 475 refills could preserve 2.8 px spacing; the required 2,171-cell refill reduces nearest-neighbour spacing (parent mean 3.735px, candidate mean 3.550px). PRUNE and spacing are therefore not perfectly separable at fixed count.
- **Evidence:** Catalogue hide/recover and SGMC results in `evidence/r0-prune3-run-card.json` are **PROXY**, never scores or gates. R0's 0.2778 remains **CLAIM** until a receipt is supplied.
