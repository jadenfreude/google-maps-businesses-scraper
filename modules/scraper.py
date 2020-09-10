from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC

from modules.helpers import *
from modules.settings import SETTINGS

import time
import xlsxwriter

def scrape(args):
    if args.pages is not None:
        SETTINGS["PAGE_DEPTH"] = args.pages
    SETTINGS["BASE_QUERY"] = args.query
    SETTINGS["PLACES"] = args.places.split(',')

    # Created driver and wait
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)

    # Set main box class name
    BOX_CLASS = "section-result-content"

    # Initialize workbook / worksheet
    workbook = xlsxwriter.Workbook('ScrapedData_GoogleMaps.xlsx')
    worksheet = workbook.add_worksheet()
    headers = generate_headers(args)
    print_table_headers(worksheet, headers)

    # Start from second row in xlsx, as first one is reserved for headers
    row = 1

    # Remember scraped addresses to skip duplicates
    addresses_scraped = []

    start_time = time.time()

    for place in SETTINGS["PLACES"]:
        # Go to the index page
        driver.get(SETTINGS["MAPS_INDEX"])
        
        # Build the query string
        query = "{0} {1}".format(SETTINGS["BASE_QUERY"], place)
        print("Moving on to {0}".format(place))

        # Fill in the input and press enter to search
        q_input = driver.find_element_by_name("q")
        q_input.send_keys(query, Keys.ENTER)
        
        # Wait for the results page to load
        _ = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, BOX_CLASS))
        )

        # Loop through pages and results
        for _ in range(0, SETTINGS["PAGE_DEPTH"]):
            # Get all the results boxes
            boxes = driver.find_elements_by_class_name(BOX_CLASS)

            # Loop through all boxes and get the info from it and store into an excel
            for box in boxes:
                name = box.find_element_by_class_name("section-result-title").find_element_by_xpath(".//span[1]").text

                address = box.find_element_by_class_name("section-result-location").text

                if address in addresses_scraped and not args.skip_duplicate_addresses:
                    print("Skipping {0} as duplicate by address".format(name))
                else:
                    data = []
                    data.append(name)
                    addresses_scraped.append(address)
        
                    # Just to have something to follow the progress
                    print("Currently scraping on: {0}".format(name))

                    phone = box.find_element_by_class_name("section-result-phone-number").find_element_by_xpath(".//span[1]").text
                    data.append(phone)

                    data.append(address)
                    
                    if args.scrape_website:
                        url = box.find_element_by_class_name("section-result-action-icon-container").find_element_by_xpath("./..").get_attribute("href")
                        website = get_website_url(url)
                        data.append(website)
                    
                    write_data_row(worksheet, data, row)
                    row += 1

            # Go to next page                                
            next_page_link = driver.find_element_by_class_name("n7lv7yjyC35__button-next-icon")
            try:
                next_page_link.click()
            except WebDriverException:
                print("No more pages, navigation not clickable")
                break

            # Wait for the next page to load
            time.sleep(5)
        print("-------------------")

    workbook.close()
    driver.close()

    end_time = time.time()
    print("Done. Time it took was {0}s".format((end_time-start_time)))