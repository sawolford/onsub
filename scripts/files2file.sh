#!/bin/sh
echo "all = ["
sed 's,/[^/]*$,,' | sort | uniq | sed 's/^/   ("/' | sed 's/$/"),/'
echo "]"
