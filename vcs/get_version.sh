#!/usr/bin/env bash
git describe --tags
status=$?
if [ "$status" -ne 0 ]; then
    echo ""
    exit $status
fi

