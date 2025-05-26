#!/bin/sh

rm -f matches.db
sqlite3 matches.db < schema.sql
sqlite3 matches.db < data.sql