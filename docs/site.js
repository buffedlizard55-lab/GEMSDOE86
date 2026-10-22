(() => {
  const byId = (id) => document.getElementById(id);

  async function loadBoard() {
    const body = byId("leaderboard-body");
    if (!body) return;
    try {
      const response = await fetch("data/leaderboard.json", { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      body.replaceChildren();
      for (const entry of (data.rows || []).slice(0, 10)) {
        const row = document.createElement("tr");
        const rank = document.createElement("td");
        const participant = document.createElement("td");
        const score = document.createElement("td");
        const evidence = document.createElement("td");
        rank.textContent = String(entry.rank);
        participant.textContent = entry.participant;
        score.textContent = Number(entry.score).toFixed(4);
        const label = document.createElement("span");
        label.className = "score-label";
        label.textContent = entry.evidence_class || data.evidence_class || "UNLABELLED";
        evidence.append(label);
        row.append(rank, participant, score, evidence);
        body.append(row);
      }
      const date = data.fetched_on_utc_date || data.fetched_at_utc || "date not recorded";
      const updated = byId("leaderboard-updated");
      if (updated) updated.textContent = `Official public board snapshot: ${date}. Not a GEMSDOE86 result or receipt.`;
      const top = (data.rows || [])[0];
      if (top && byId("leaderboard-leader")) {
        byId("leaderboard-leader").textContent = `${top.participant} · ${Number(top.score).toFixed(4)}`;
      }
    } catch (error) {
      const updated = byId("leaderboard-updated");
      if (updated) updated.textContent = "Leaderboard feed could not be refreshed in this browser; see the checked-in snapshot and source link.";
    }
  }

  async function gateDownload() {
    const anchor = byId("submission-download");
    const status = byId("download-status");
    if (!anchor || !status) return;
    try {
      const response = await fetch("data/run-card.json", { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const card = await response.json();
      const checkNames = [
        "source_data_provenance_authorized",
        "template_grid_and_dimensions_match",
        "crs_epsg_32611",
        "pixel_size_100m",
        "single_band_float32",
        "values_finite_and_within_0_to_1",
        "footprint_and_catalogue_support",
        "visible_fault_pixels_masked_exactly",
        "surface_uniqueness_passed",
        "final_raster_uniqueness_passed",
        "on_disk_tiff_validated_by_shared_writer",
        "one_tiff_zip_and_receipt_written_atomically",
      ];
      const checks = checkNames.map((name) => card.validator?.checks?.[name]);
      const ci = card.holdout?.ci95;
      const holdoutEvidencePresent = card.holdout?.evidence_class === "HOLDOUT-DTI"
        && typeof card.holdout?.evaluator_version === "string"
        && Number.isInteger(card.holdout?.withheld_positive_pixels)
        && card.holdout.withheld_positive_pixels > 0
        && typeof card.holdout?.pooled_dti === "number"
        && Number.isFinite(card.holdout.pooled_dti)
        && card.holdout.pooled_dti >= 0 && card.holdout.pooled_dti <= 1
        && Array.isArray(ci) && ci.length === 2 && ci.every((value) => typeof value === "number" && Number.isFinite(value))
        && ci[0] <= ci[1];
      const surfaceCorr = card.uniqueness?.surface_max_spearman_rank_correlation;
      const rasterCorr = card.uniqueness?.final_raster_max_spearman_rank_correlation;
      const dotOverlap = card.uniqueness?.max_3px_dot_overlap_fraction;
      const uniquenessEvidencePresent = [surfaceCorr, rasterCorr, dotOverlap].every((value) => typeof value === "number" && Number.isFinite(value))
        && surfaceCorr <= 0.9 && rasterCorr <= 0.9 && dotOverlap <= 0.7;
      const safePath = typeof card.artifact?.tiff_path === "string"
        && /^downloads\/[A-Za-z0-9._-]+\.tif$/.test(card.artifact.tiff_path)
        && typeof card.artifact?.tiff_sha256 === "string"
        && /^[a-f0-9]{64}$/i.test(card.artifact.tiff_sha256);
      const safeZip = typeof card.artifact?.zip_path === "string"
        && /^downloads\/[A-Za-z0-9._-]+\.zip$/.test(card.artifact.zip_path)
        && typeof card.artifact?.zip_sha256 === "string"
        && /^[a-f0-9]{64}$/i.test(card.artifact.zip_sha256);
      const safeReceipt = typeof card.artifact?.writer_receipt_path === "string"
        && /^downloads\/[A-Za-z0-9._-]+\.json$/.test(card.artifact.writer_receipt_path)
        && typeof card.artifact?.writer_receipt_sha256 === "string"
        && /^[a-f0-9]{64}$/i.test(card.artifact.writer_receipt_sha256);
      const allChecksPass = checks.length === checkNames.length && checks.every((value) => value === true);
      const ready = card.artifact?.download_available === true
        && card.artifact?.submission_safe === true
        && card.holdout?.status === "PASS"
        && holdoutEvidencePresent
        && card.uniqueness?.status === "PASS"
        && uniquenessEvidencePresent
        && typeof card.uniqueness?.registry_index_sha256 === "string"
        && /^[a-f0-9]{64}$/i.test(card.uniqueness.registry_index_sha256)
        && card.validator?.status === "PASS"
        && card.validator?.shared_submission_writer_used === true
        && safePath && safeZip && safeReceipt
        && allChecksPass;
      if (ready) {
        anchor.href = card.artifact.tiff_path;
        anchor.removeAttribute("aria-disabled");
        anchor.classList.remove("disabled");
        anchor.setAttribute("download", "");
        anchor.textContent = "Download validated submission TIFF";
        const zipLink = byId("zip-download");
        const receiptLink = byId("receipt-download");
        if (zipLink) { zipLink.href = card.artifact.zip_path; zipLink.setAttribute("download", ""); }
        if (receiptLink) { receiptLink.href = card.artifact.writer_receipt_path; receiptLink.setAttribute("download", ""); }
        if (byId("archive-downloads")) byId("archive-downloads").hidden = false;
        status.textContent = "PASS — shared evaluator, uniqueness gate, and shared-writer checks are recorded in the run card.";
        status.classList.remove("notice");
        const pill = byId("readiness-pill");
        if (pill) { pill.textContent = "Ready to submit"; pill.classList.add("ready"); }
        if (byId("blocked-title")) byId("blocked-title").textContent = "Validated submission file ready — follow the executive instructions.";
        if (byId("blocked-copy")) byId("blocked-copy").textContent = "The evidence gate is recorded. Download only the file named in the run card and shared-writer receipt; organizer confirmation still follows upload.";
        if (byId("holdout-status")) byId("holdout-status").textContent = "Passed · HOLDOUT-DTI";
        if (byId("leakage-status")) byId("leakage-status").textContent = "Cleared";
        if (byId("uniqueness-status")) byId("uniqueness-status").textContent = "Passed";
        if (byId("tiff-status")) byId("tiff-status").textContent = "Download ready";
        if (byId("slot-status")) byId("slot-status").textContent = "Selector decision pending";
      }
    } catch (_) {
      // Fail closed. The static blocked state remains visible if the run card is missing or invalid.
    }
  }

  loadBoard();
  gateDownload();
})();
