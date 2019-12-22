#!/bin/sh
echo "all = ["
sort | uniq | sed 's/^/   ("/' | sed 's/$/"),/'
echo "]"
