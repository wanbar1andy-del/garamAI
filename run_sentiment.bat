
@echo off
echo [GARAM] Updating Sentiment Data...
py -3.9 scripts/ingest_community_sentiment.py
echo [DONE] Sentiment Data Updated.
exit
