#!/bin/bash

case $(uname -s) in
	Linux*) ps="ps2pdf";;
	Darwin*) ps="pstopdf";;
esac

if ! command -v enscript 2>&1 >/dev/null; then
	echo "This script requires enscript to generate the pdf"
	exit 1
fi

cat schema.sql insert.sql q.sql |
enscript -B -C -Esql -fCourier10 --word-wrap -MLetter -p - |
$ps - part2.pdf

