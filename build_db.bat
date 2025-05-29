@echo off

:: Remove the database file if it exists
if exist matches.db (
    del /f matches.db
)

:: Create the database schema
sqlite3 matches.db < schema.sql

:: Insert data into the database
sqlite3 matches.db < data.sql

echo recreated db.
