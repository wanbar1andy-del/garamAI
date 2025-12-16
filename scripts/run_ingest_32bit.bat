@echo off
echo Starting Kiwoom Data Ingestion (2-Year Backfill)...
echo Target Path: c:\garam\garam\GARAM_Data\history\minute
echo Python Path: C:\Python39-32\python.exe

C:\Python39-32\python.exe pipeline/ingest/run_ingest_kiwoom.py
pause
