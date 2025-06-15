from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FILTERED_URL = "https://find.cancerresearchuk.org/clinical-trials?size=n_20_n&filters%5B0%5D%5Bfield%5D=trial_status&filters%5B0%5D%5Bvalues%5D%5B0%5D=Open&filters%5B0%5D%5Btype%5D=any&filters%5B1%5D%5Bfield%5D=cancer_types&filters%5B1%5D%5Bvalues%5D%5B0%5D=Acute%20leukaemia&filters%5B1%5D%5Bvalues%5D%5B1%5D=Acute%20lymphoblastic%20leukaemia%20%28ALL%29&filters%5B1%5D%5Bvalues%5D%5B2%5D=Acute%20myeloid%20leukaemia%20%28AML%29&filters%5B1%5D%5Bvalues%5D%5B3%5D=Blood%20cancers&filters%5B1%5D%5Bvalues%5D%5B4%5D=Chronic%20leukaemia&filters%5B1%5D%5Bvalues%5D%5B5%5D=Chronic%20lymphocytic%20leukaemia%20%28CLL%29&filters%5B1%5D%5Bvalues%5D%5B6%5D=Chronic%20myeloid%20leukaemia%20%28CML%29&filters%5B1%5D%5Bvalues%5D%5B7%5D=Hairy%20cell%20leukaemia&filters%5B1%5D%5Bvalues%5D%5B8%5D=High%20grade%20lymphoma&filters%5B1%5D%5Bvalues%5D%5B9%5D=Hodgkin%20lymphoma&filters%5B1%5D%5Bvalues%5D%5B10%5D=Leukaemia&filters%5B1%5D%5Bvalues%5D%5B11%5D=Low%20grade%20lymphoma&filters%5B1%5D%5Bvalues%5D%5B12%5D=Lymphoma&filters%5B1%5D%5Bvalues%5D%5B13%5D=Myelodysplastic%20syndrome%20%28MDS%29&filters%5B1%5D%5Bvalues%5D%5B14%5D=Myelofibrosis&filters%5B1%5D%5Bvalues%5D%5B15%5D=Myeloma&filters%5B1%5D%5Bvalues%5D%5B16%5D=Myeloproliferative%20neoplasms&filters%5B1%5D%5Bvalues%5D%5B17%5D=Non-Hodgkin%20lymphoma&filters%5B1%5D%5Bvalues%5D%5B18%5D=Thrombocythaemia&filters%5B1%5D%5Btype%5D=any"

def setup_driver():
    """Set up and return a configured Chrome WebDriver."""
    try:
        logger.info("Setting up Chrome WebDriver...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Chrome WebDriver setup complete")
        return driver
    except Exception as e:
        logger.error(f"Error setting up WebDriver: {str(e)}")
        raise

def close_cookie_banner(driver):
    # Try common selectors for cookie banners/buttons
    try:
        # OneTrust cookie banner (common in UK/EU sites)
        btn = driver.find_element(By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler')
        btn.click()
        time.sleep(1)
        logger.info('Closed cookie consent banner (OneTrust)')
        return
    except Exception:
        pass
    try:
        # Generic accept/agree button
        btn = driver.find_element(By.XPATH, "//button[contains(translate(., 'ACEPT', 'acept'), 'accept') or contains(translate(., 'AGREE', 'agree'), 'agree')]")
        btn.click()
        time.sleep(1)
        logger.info('Closed cookie consent banner (generic)')
        return
    except Exception:
        pass
    # Add more selectors as needed
    logger.info('No cookie banner found or already closed')

def extract_detail_fields(driver, url):
    """Extract detailed fields from a trial's detail page."""
    driver.get(url)
    time.sleep(2)
    close_cookie_banner(driver)
    detail = {}
    try:
        # Recruitment start date
        try:
            start_panel = driver.find_element(By.CSS_SELECTOR, "div.pane-node-field-trial-recruitment-start")
            time_tag = start_panel.find_element(By.CSS_SELECTOR, "time")
            detail["recruitment_start"] = time_tag.text.strip()
            detail["recruitment_start_iso"] = time_tag.get_attribute("datetime")
        except Exception as e:
            detail["recruitment_start"] = ""
            detail["recruitment_start_iso"] = ""
        # Recruitment end date
        try:
            end_panel = driver.find_element(By.CSS_SELECTOR, "div.pane-node-field-trial-recruitment-end")
            time_tag = end_panel.find_element(By.CSS_SELECTOR, "time")
            detail["recruitment_end"] = time_tag.text.strip()
            detail["recruitment_end_iso"] = time_tag.get_attribute("datetime")
        except Exception as e:
            detail["recruitment_end"] = ""
            detail["recruitment_end_iso"] = ""
        # Chief Investigator
        try:
            chief = driver.find_element(By.XPATH, "//*[contains(text(),'Chief Investigator')]/following-sibling::*[1]")
            detail["chief_investigator"] = chief.text.strip()
        except:
            pass
        # Supported by
        try:
            supported = driver.find_element(By.XPATH, "//*[contains(text(),'Supported by')]/following-sibling::*[1]")
            detail["supported_by"] = supported.text.strip()
        except:
            pass
        # Contact info
        try:
            phone = driver.find_element(By.XPATH, "//*[contains(text(),'Freephone')]")
            detail["contact_phone"] = phone.text.strip()
        except:
            pass
        try:
            email = driver.find_element(By.XPATH, "//a[contains(@href, 'mailto:')]")
            email_addr = email.get_attribute("href").replace("mailto:", "")
            if '@' in email_addr:
                detail["contact_email"] = email_addr
            else:
                detail["contact_email"] = None
        except:
            detail["contact_email"] = None
        # Updated: 'Who can enter' panel
        try:
            who_header = driver.find_element(By.XPATH, "//h2[contains(@class, 'accordion-header') and contains(., 'Who can enter')]")
            # Click to expand if not already expanded
            parent_div = who_header.find_element(By.XPATH, "..")
            if 'expanded' not in parent_div.get_attribute('class'):
                who_header.click()
                time.sleep(1)
            # Now extract the content from the field-item
            who_panel = parent_div.find_element(By.CSS_SELECTOR, "div.field-item[property='schema:population']")
            detail["who_can_enter"] = who_panel.text.strip()
        except Exception as e:
            logger.error(f"Could not extract 'Who can enter': {str(e)}")
            detail["who_can_enter"] = ""
        # Updated: 'Location' panel (similar logic, fallback to previous logic)
        try:
            loc_header = driver.find_element(By.XPATH, "//h2[contains(@class, 'accordion-header') and contains(., 'Location')]")
            parent_div = loc_header.find_element(By.XPATH, "..")
            if 'expanded' not in parent_div.get_attribute('class'):
                loc_header.click()
                time.sleep(1)
            loc_panel = parent_div.find_element(By.CSS_SELECTOR, "div.accordion-body")
            detail["location_panel"] = loc_panel.text.strip()
        except Exception as e:
            logger.error(f"Could not extract 'Location': {str(e)}")
            detail["location_panel"] = ""
    except Exception as e:
        logger.error(f"Error extracting detail fields from {url}: {str(e)}")
    return detail

def scrape_trials():
    driver = None
    try:
        driver = setup_driver()
        trials = []
        logger.info(f"Navigating to {FILTERED_URL}")
        driver.get(FILTERED_URL)
        time.sleep(5)
        close_cookie_banner(driver)

        trial_summaries = []
        page_num = 1
        while True:
            logger.info(f"Scraping page {page_num}...")
            # Wait for trial cards to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.chakra-card"))
            )
            trial_cards = driver.find_elements(By.CSS_SELECTOR, "a.chakra-card")
            logger.info(f"Found {len(trial_cards)} trial cards on page {page_num}.")

            # Step 1: Collect all links and summary info for this page
            for i, card in enumerate(trial_cards):
                try:
                    link = card.get_attribute("href")
                    title = card.find_element(By.CSS_SELECTOR, "h2.chakra-heading").text
                    type_text = card.find_element(By.CSS_SELECTOR, "p.chakra-text.label-text").text
                    p_tags = card.find_elements(By.CSS_SELECTOR, "p.chakra-text")
                    description = ""
                    status = ""
                    cancer_types = ""
                    locations = ""
                    for p in p_tags:
                        text = p.text
                        if text.startswith("Status:"):
                            status = text.replace("Status:", "").strip()
                        elif text.startswith("Cancer type(s):"):
                            cancer_types = text.replace("Cancer type(s):", "").strip()
                        elif text.startswith("Locations:"):
                            locations = text.replace("Locations:", "").strip()
                        elif text and text != type_text and not description:
                            description = text
                    trial_summaries.append({
                        "title": title,
                        "type": type_text,
                        "description": description,
                        "status": status,
                        "cancer_types": cancer_types,
                        "locations": locations,
                        "link": link
                    })
                except Exception as e:
                    logger.error(f"Error collecting summary for trial {i+1} on page {page_num}: {str(e)}")
                    continue

            # Check for "Next" button (pagination)
            try:
                # Wait for pagination to be present
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.rc-pagination"))
                )
                
                # Find the next button - using multiple possible selectors
                next_btn = None
                for selector in [
                    "li.rc-pagination-next:not(.rc-pagination-disabled)",
                    "button[aria-label='Next Page']",
                    "//li[contains(@class, 'rc-pagination-next') and not(contains(@class, 'rc-pagination-disabled'))]"
                ]:
                    try:
                        if selector.startswith("//"):
                            next_btn = driver.find_element(By.XPATH, selector)
                        else:
                            next_btn = driver.find_element(By.CSS_SELECTOR, selector)
                        if next_btn:
                            break
                    except:
                        continue

                if not next_btn:
                    logger.info("No more pages to scrape (Next button not found or disabled).")
                    break

                # Scroll to the button to ensure it's clickable
                driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                time.sleep(1)

                # Try to click the button
                try:
                    next_btn.click()
                except:
                    # If regular click fails, try JavaScript click
                    driver.execute_script("arguments[0].click();", next_btn)

                # Wait for the page to load
                time.sleep(3)
                
                # Verify we're on a new page by checking if the first trial card is different
                new_cards = driver.find_elements(By.CSS_SELECTOR, "a.chakra-card")
                if not new_cards:
                    logger.info("No new cards found after clicking next, assuming last page.")
                    break
                
                page_num += 1
                
            except Exception as e:
                logger.error(f"Error during pagination: {str(e)}")
                break

        # Step 2: For each link, visit the detail page and extract more info
        for i, trial in enumerate(trial_summaries):
            try:
                detail = extract_detail_fields(driver, trial["link"])
                trial.update(detail)
                trials.append(trial)
                logger.info(f"Extracted trial {i+1}: {trial['title']}")
            except Exception as e:
                logger.error(f"Error extracting detail for trial {i+1}: {str(e)}")
                continue
        with open("clinical_trials.json", "w") as f:
            json.dump(trials, f, indent=2)
        logger.info(f"Successfully scraped {len(trials)} trials.")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        if driver:
            logger.error("Page source at time of error:")
            logger.error(driver.page_source[:1000])
    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver closed")

if __name__ == "__main__":
    scrape_trials() 