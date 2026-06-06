#!/usr/bin/env bash
set -euo pipefail

compose=(docker compose)

echo "Checking authorized AXFR from dns-slave..."
authorized_output="$("${compose[@]}" exec -T dns-slave dig @dns-master internal AXFR +noall +answer)"

grep -Fq "web.internal." <<<"$authorized_output"
grep -Fq "10.10.0.20" <<<"$authorized_output"

echo "Checking that dns-client cannot perform AXFR..."
unauthorized_output="$("${compose[@]}" exec -T dns-client dig @dns-master internal AXFR +noall +comments +answer)"

grep -Fq "status: REFUSED" <<<"$unauthorized_output"

echo "Checking that the transferred zone is served by dns-slave..."
slave_answer="$("${compose[@]}" exec -T dns-client dig @dns-slave web.internal A +short)"

grep -Fxq "10.10.0.20" <<<"$slave_answer"

echo "AXFR checks passed."
