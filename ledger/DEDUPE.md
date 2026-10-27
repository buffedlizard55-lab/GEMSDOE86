# Ledger identity record

Source: `registry/prior_scores.csv` (133 rows). Grouped into 133 exact same-site name groups.

Different names, fill suffixes and sites are never collapsed merely because
they share a filename token. Local SHA-256 is attached only to an exact
same-site filename association; it is not an organizer receipt or proof of
what bytes were uploaded. Conflicting same-name scores stop generation.

| name | duplicate identical claims |
|---|---|
