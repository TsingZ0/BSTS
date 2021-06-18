#!/bin/bash

# several minutes
python PreProcessing.py

# several hours
python Postings.py

# several minutes
python AllWords.py
python BuildWordDict.py
python DocIdx.py

# start the search engine and web interface
python Search.py