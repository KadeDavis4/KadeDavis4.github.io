#Allows user to enter a static website URL, apply filters if desired, and download all csv files returned
#Intentionally contains a mix of python built-ins, learned tricks, and ground-up logic 

import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup #pip install requests beautifulsoup4 - if not instealled
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser
import time
import sys
import os


HEADERS = {"User-Agent": "KDScraper/1.0 (kadedavis99@gmail.com)"}

def scrape(URL, filters):
    """
    Reads static website and returns all csv or csv.gz download links, with an optional filter for links with specific words
    """

    #Check to make sure parsing is ok
    robots_txt = RobotFileParser(urljoin(URL, "/robots.txt"))
    robots_txt.read()
    if not robots_txt.can_fetch("KDScraper/1.0", URL):
        print("Website does not permit parsing. cancelling parse")
        return []

    #Load website and handle errors
    try:
        output = requests.get(URL, headers=HEADERS, timeout=15)
        output.raise_for_status()
    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return []
    except Exception as err:
        print(f"Other error occurred: {err}")
        return []

    #Load into beautifulsoup object
    soup_output = BeautifulSoup(output.text, "html.parser")

    #Get all links from output
    links = soup_output.find_all("a", href=True)

    #Filter out links for csv and filters
    csv_links = []
    for link in links:
        href = link.get("href")
        if href.endswith(".csv") or href.endswith(".csv.gz"):
            if len(filters) > 0:
                if all(filt.lower() in href.lower() for filt in filters):
                    full_url = urljoin(URL, href)
                    csv_links.append(full_url)

            else:
                full_url = urljoin(URL, href)
                csv_links.append(full_url)

    return csv_links

def download(links):
    """
    Takes a list of download links, displays them, and allows the user to download them to a new "downloaded_files" folder
    """

    print("Download links returned:\n")
    for link in links:
        print (f"{link}")
    
    retry_loop = True
    while retry_loop:
        download_or_retry = input("Enter 1 to download or 2 to retry: ")
        if download_or_retry == "1":
            os.makedirs("downloaded_files", exist_ok=True)
            files = 0
            for link in links:
                try:
                    file_name = link.split("/")[-1]
                    output_path = os.path.join("downloaded_files", file_name)

                    #Handles duplicate file names
                    name, extension = file_name.split(".", 1)
                    counter = 1
                    while os.path.exists(output_path):
                        output_path = os.path.join("downloaded_files", f"{name}_{counter}.{extension}")
                        counter += 1

                    #Avoids writing entire file to memory
                    with requests.get(link, headers=HEADERS, timeout=30 ,stream=True) as response:
                        response.raise_for_status()
                        with open(output_path, "wb") as file:
                            for chunk in response.iter_content(chunk_size=8192):
                                file.write(chunk)

                    files += 1
                except Exception as e:
                    print(f"Issue with link ({link}) with error: {e}")
            print(f"{files} files downloaded to {os.getcwd()}/downloaded_files/")
            retry_loop = False
                
        elif download_or_retry == "2":
            retry_loop = False
        else:
            continue

            
        
#-- UI Loop --
if __name__ == "__main__":
    #Initial first-time URL ask, allows cleaner ask later
    URL = input("Note: Must be parsable and must include downloadable csv file(s)\nPlease also read website TOS and ensure no improper scraper use before entering URL\nEnter URL: ")
    while True:
        

        #Get filters. Parser will only return downloads with entered string within full link
        filters = []
        filter_loop = True
        while filter_loop:
            temp_filter = input("Enter filter or enter nothing to continue: ")
            if temp_filter == "":
                filter_loop = False
                continue
            filters.append(temp_filter)
            if len(filters) > 0:
                print(f"Filters: {filters}")

        #Program running reporting
        filter_reporting = ""
        if len(filters) > 0:
            filter_reporting = f"with filters: {filters}"
        print (f"Scraping {URL} {filter_reporting}")
        time.sleep(1)

        #Download Loop
        try:
            links = scrape(URL, filters)
            if len(links) == 0:
                print("No links returned. Try again")
            else:
                download(links)
        except Exception as e:
            print(e)

        URL = input("Enter new URL or enter 0 to exit: ")
        if URL == "0":
            sys.exit(0)
