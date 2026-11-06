#!/usr/bin/env bash
set -e  # stop on the first failure so you don't end up half-moved

mkdir -p pages css images downloads/analysis downloads/python downloads/other

# pages + css
git mv analysis.html database.html python.html pages/
git mv style.css css/

# images (renamed, no spaces)
git mv "Screenshot 2026-08-05 163411.png" images/file-sorter.png
git mv csv_merger.jpg       images/csv-merger.jpg
git mv ReportGenerator.jpg  images/report-generator.jpg

# downloads
git mv Resume.pdf downloads/
git mv airbnb_data_cleaning.py downloads/analysis/
git mv ExchangeRates.py FileSorter.py HashMap.zip ReportGenerator.zip \
       csv_merger.py csv_web_scraper.py duplicate_row_finder.py \
       excel_csv_converter.py file_renamer.py pdf_text_extractor.py \
       tsp_algorithm.py downloads/python/
git mv "Excel Sample.xlsx" downloads/other/excel-sample.xlsx
git mv WebPage.zip smallsh.c downloads/other/

# unused files -- uncomment if you want them gone (still recoverable from git history)
# git rm "Black jpg.jpg" ExchangeImage.png Request.py
