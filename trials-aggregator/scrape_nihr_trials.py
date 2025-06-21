from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://bepartofresearch.nihr.ac.uk/results/search-results?query=Leukemia&location="

def setup_driver():
    """Set up and return a configured Chrome WebDriver."""
    try:
        logger.info("Setting up Chrome WebDriver...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Back to headless for production
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info("Chrome WebDriver setup complete")
        return driver
    except Exception as e:
        logger.error(f"Error setting up WebDriver: {str(e)}")
        raise

def close_cookie_banner(driver):
    """Close cookie consent banners if they appear."""
    try:
        # Wait a bit for the cookie banner to potentially appear
        time.sleep(2)
        
        # Try common selectors for cookie banners
        cookie_selectors = [
            'button[contains(text(), "Accept")]',
            'button[contains(text(), "Accept additional cookies")]',
            'button[contains(text(), "I agree")]',
            'button[contains(text(), "OK")]',
            'button#accept-cookies',
            'button.accept-cookies',
            '.cookie-banner button',
            '[data-testid="cookie-accept"]'
        ]
        
        for selector in cookie_selectors:
            try:
                if selector.startswith('[') or selector.startswith('.') or selector.startswith('#'):
                    btn = driver.find_element(By.CSS_SELECTOR, selector)
                else:
                    # Extract text from selector for XPath
                    text_content = selector.split('"')[1] if '"' in selector else selector
                    btn = driver.find_element(By.XPATH, f"//button[contains(text(), '{text_content}')]")
                
                if btn.is_displayed() and btn.is_enabled():
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                    logger.info(f'Closed cookie consent banner using: {selector}')
                    return
            except Exception:
                continue
                
    except Exception as e:
        logger.info(f'No cookie banner found or could not close: {str(e)}')

def scroll_to_load_all_trials(driver):
    """Scroll to the bottom of the page repeatedly to load all trials via infinite scroll."""
    logger.info("Starting infinite scroll to load all trials...")
    
    previous_trial_count = 0
    scroll_attempts = 0
    max_scroll_attempts = 50  # Prevent infinite loops
    no_change_attempts = 0
    max_no_change = 5  # Stop if no new trials loaded after 5 attempts
    
    while scroll_attempts < max_scroll_attempts and no_change_attempts < max_no_change:
        # Scroll to bottom of page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # Wait for content to load
        
        # Count current number of trial articles
        try:
            trial_articles = driver.find_elements(By.CSS_SELECTOR, "article[data-v-204c41ad]")
            current_trial_count = len(trial_articles)
            
            logger.info(f"Scroll attempt {scroll_attempts + 1}: Found {current_trial_count} trials")
            
            if current_trial_count == previous_trial_count:
                no_change_attempts += 1
                logger.info(f"No new trials loaded (attempt {no_change_attempts}/{max_no_change})")
            else:
                no_change_attempts = 0  # Reset counter if we found new trials
                
            previous_trial_count = current_trial_count
            scroll_attempts += 1
            
        except Exception as e:
            logger.error(f"Error counting trials during scroll: {str(e)}")
            scroll_attempts += 1
    
    logger.info(f"Finished scrolling. Total trials found: {previous_trial_count}")
    return previous_trial_count

def extract_trial_details(driver, trial_element):
    """Extract details from a single trial element."""
    trial_data = {}
    
    try:
        # Extract title
        try:
            title_element = trial_element.find_element(By.CSS_SELECTOR, "h2 a")
            trial_data["title"] = title_element.text.strip()
            trial_data["link"] = title_element.get_attribute("href")
        except Exception as e:
            logger.error(f"Could not extract title: {str(e)}")
            trial_data["title"] = ""
            trial_data["link"] = ""
        
        # Extract description/summary
        try:
            description_element = trial_element.find_element(By.CSS_SELECTOR, "p")
            trial_data["description"] = description_element.text.strip()
        except Exception:
            trial_data["description"] = ""
        
        # Extract study type (default for NIHR)
        trial_data["type"] = "Clinical trial"
        
        # Extract status (default to Open for NIHR active studies)
        trial_data["status"] = "Open"
        
        # Extract cancer types - look for keywords in title and description
        cancer_keywords = []
        text_to_search = (trial_data["title"] + " " + trial_data["description"]).lower()
        
        # Common cancer/leukemia terms
        cancer_terms = [
            "acute myeloid leukaemia", "aml", "acute lymphoblastic leukaemia", "all",
            "chronic myeloid leukaemia", "cml", "chronic lymphocytic leukaemia", "cll",
            "myelodysplastic syndrome", "mds", "myeloma", "lymphoma", "leukaemia", "leukemia",
            "blood cancer", "haematological", "hematological"
        ]
        
        for term in cancer_terms:
            if term in text_to_search:
                cancer_keywords.append(term.title())
        
        trial_data["cancer_types"] = ", ".join(set(cancer_keywords)) if cancer_keywords else "Blood cancers, Leukaemia"
        
        # Extract location information
        try:
            # Look for location information in various possible places
            location_text = ""
            
            # Try to find location in the trial element
            location_elements = trial_element.find_elements(By.CSS_SELECTOR, "[class*='location'], [class*='Location']")
            if location_elements:
                location_text = location_elements[0].text.strip()
            
            # If no specific location found, set default
            if not location_text:
                location_text = "Multiple healthcare locations around the world"
                
            trial_data["locations"] = location_text
            
        except Exception:
            trial_data["locations"] = "Multiple healthcare locations around the world"
        
        # Set default values for fields that match CRUK structure but aren't easily extractable from summary
        trial_data["recruitment_start"] = ""
        trial_data["recruitment_start_iso"] = ""
        trial_data["recruitment_end"] = ""
        trial_data["recruitment_end_iso"] = ""
        trial_data["chief_investigator"] = ""
        trial_data["supported_by"] = ""
        trial_data["contact_phone"] = ""
        trial_data["contact_email"] = ""
        trial_data["who_can_enter"] = ""  # Will be populated from detail page
        trial_data["location_panel"] = trial_data["locations"]
        
    except Exception as e:
        logger.error(f"Error extracting trial details: {str(e)}")
        
    return trial_data

def extract_detailed_info(driver, trial_data):
    """Visit the trial detail page to extract additional information."""
    if not trial_data.get("link"):
        return trial_data
        
    try:
        logger.info(f"Extracting detailed info for: {trial_data['title']}")
        driver.get(trial_data["link"])
        time.sleep(4)  # Give page time to load
        
        # Close any cookie banners on the detail page
        close_cookie_banner(driver)
        
        # Extract detailed eligibility criteria
        eligibility_text = extract_who_can_take_part(driver)
        if eligibility_text:
            trial_data["who_can_enter"] = eligibility_text
        
        # Extract contact information
        extract_contact_info(driver, trial_data)
        
        # Extract dates and other details
        extract_study_dates(driver, trial_data)
        
    except Exception as e:
        logger.error(f"Error visiting detail page for {trial_data.get('title', 'Unknown')}: {str(e)}")
        
    return trial_data

def extract_who_can_take_part(driver):
    """Extract and expand the 'Who can take part?' section to get inclusion/exclusion criteria."""
    try:
        # First, try to find and click the "Who can take part?" section to expand it
        logger.info("Looking for 'Who can take part?' section...")
        
        # Different possible selectors for the collapsible header
        who_selectors = [
            "//h3[contains(text(), 'Who can take part')]",
            "//h2[contains(text(), 'Who can take part')]",
            "//div[contains(@class, 'collapsible')]//h3[contains(text(), 'Who can take part')]",
            "//button[contains(text(), 'Who can take part')]",
            "//*[contains(text(), 'Who can take part')][self::h1 or self::h2 or self::h3 or self::h4 or self::button]"
        ]
        
        who_header = None
        for selector in who_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        who_header = element
                        logger.info(f"Found 'Who can take part?' header using: {selector}")
                        break
                if who_header:
                    break
            except Exception as e:
                continue
        
        if not who_header:
            logger.warning("Could not find 'Who can take part?' section header")
            # Fallback - try to extract any eligibility text from the page
            return extract_fallback_eligibility(driver)
        
        # Try to click the header to expand the section
        try:
            # Scroll to the element first
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", who_header)
            time.sleep(1)
            
            # Try clicking
            who_header.click()
            time.sleep(3)  # Wait for expansion
            logger.info("Clicked to expand 'Who can take part?' section")
        except Exception as e:
            logger.info(f"Could not click to expand section: {str(e)}")
        
        # Now try to extract the content
        eligibility_text = ""
        
        # Look for content in various ways
        content_methods = [
            # Method 1: Look for content after the header
            lambda: extract_content_after_header(driver, who_header),
            # Method 2: Look for any expanded content on the page
            lambda: extract_expanded_content(driver),
            # Method 3: Extract all text and filter for eligibility criteria
            lambda: extract_fallback_eligibility(driver)
        ]
        
        for i, method in enumerate(content_methods, 1):
            try:
                result = method()
                if result and len(result.strip()) > 50:  # Only accept substantial content
                    logger.info(f"Successfully extracted eligibility criteria using method {i}")
                    eligibility_text = result
                    break
            except Exception as e:
                logger.warning(f"Method {i} failed: {str(e)}")
                continue
        
        return eligibility_text.strip()
        
    except Exception as e:
        logger.error(f"Error in extract_who_can_take_part: {str(e)}")
        return ""

def extract_content_after_header(driver, header):
    """Extract content that appears after the Who can take part header."""
    try:
        # Look for content in sibling elements or parent containers
        content_selectors = [
            "./following-sibling::div[1]",
            "./following-sibling::div[contains(@class, 'content')]",
            "./following-sibling::div[contains(@class, 'collapsible')]",
            "../following-sibling::div[1]",
            "../..//div[contains(@class, 'content')]"
        ]
        
        for selector in content_selectors:
            try:
                content_div = header.find_element(By.XPATH, selector)
                if content_div and content_div.text.strip():
                    text = content_div.text.strip()
                    if any(keyword in text.lower() for keyword in ['inclusion', 'exclusion', 'criteria', 'eligible', 'can take part']):
                        return text
            except:
                continue
        
        return ""
    except Exception as e:
        logger.error(f"Error in extract_content_after_header: {str(e)}")
        return ""

def extract_expanded_content(driver):
    """Look for any expanded collapsible content on the page."""
    try:
        # Look for expanded sections that might contain eligibility criteria
        expanded_selectors = [
            "//div[contains(@class, 'collapsible') and not(contains(@class, 'collapsed'))]",
            "//div[contains(@class, 'expanded')]//div[contains(@class, 'content')]",
            "//div[contains(@style, 'display: block')]//p[contains(text(), 'criteria') or contains(text(), 'eligible')]"
        ]
        
        for selector in expanded_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and any(keyword in text.lower() for keyword in ['inclusion', 'exclusion', 'criteria', 'can take part']):
                        return text
            except:
                continue
        
        return ""
    except Exception as e:
        logger.error(f"Error in extract_expanded_content: {str(e)}")
        return ""

def extract_fallback_eligibility(driver):
    """Fallback method to extract eligibility information from anywhere on the page."""
    try:
        # Get all text from the page and look for eligibility patterns
        page_text = driver.page_source
        
        # Look for specific patterns in the HTML
        eligibility_patterns = [
            r'Inclusion Criteria:?\s*([^`]*?)(?:You may not be able|Where can I take part|Contact information|var temp2|Funders/Sponsors)',
            r'You can take part if:?\s*([^`]*?)(?:You cannot|Exclusion|You may not be able|Where can I take part)',
            r'Eligibility:?\s*([^`]*?)(?:Contact|Study|Where can I take part)'
        ]
        
        for pattern in eligibility_patterns:
            matches = re.findall(pattern, page_text, re.DOTALL | re.IGNORECASE)
            if matches:
                # Clean up HTML tags and return the first substantial match
                import html
                clean_text = re.sub(r'<[^>]+>', ' ', matches[0])
                clean_text = html.unescape(clean_text)
                # Remove JavaScript and other artifacts
                clean_text = re.sub(r'var\s+\w+\s*=.*?;', '', clean_text, flags=re.DOTALL)
                clean_text = re.sub(r'document\..*?;', '', clean_text)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                
                # Only return if it's substantial content and contains eligibility info
                if (len(clean_text) > 100 and 
                    any(keyword in clean_text.lower() for keyword in ['inclusion', 'exclusion', 'criteria', 'participants'])):
                    return clean_text
        
        return ""
    except Exception as e:
        logger.error(f"Error in extract_fallback_eligibility: {str(e)}")
        return ""

def extract_contact_info(driver, trial_data):
    """Extract contact information from the detail page."""
    try:
        # Look for contact information
        contact_selectors = [
            "//div[contains(@class, 'contact')]",
            "//*[contains(text(), 'Contact')]",
            "//div[contains(@class, 'study-contact')]"
        ]
        
        for selector in contact_selectors:
            try:
                contact_section = driver.find_element(By.XPATH, selector)
                contact_text = contact_section.text
                
                # Extract email
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, contact_text)
                if emails:
                    trial_data["contact_email"] = emails[0]
                
                # Extract phone number
                phone_patterns = [
                    r'(\+44[\s-]?[0-9\s-]{10,})',
                    r'(0[0-9\s-]{10,})',
                    r'(\+[0-9\s-]{10,})'
                ]
                
                for pattern in phone_patterns:
                    phones = re.findall(pattern, contact_text)
                    if phones:
                        trial_data["contact_phone"] = phones[0].strip()
                        break
                        
                break
            except:
                continue
                
    except Exception as e:
        logger.error(f"Error extracting contact info: {str(e)}")

def extract_study_dates(driver, trial_data):
    """Extract study dates from the detail page."""
    try:
        page_text = driver.page_source.lower()
        
        # Look for date patterns
        date_patterns = [
            (r'start[ed\s]*date[:\s]*([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{4})', 'recruitment_start'),
            (r'end[s\s]*date[:\s]*([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{4})', 'recruitment_end'),
            (r'recruitment[:\s]*([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{4})', 'recruitment_start')
        ]
        
        for pattern, field in date_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                trial_data[field] = matches[0]
                
    except Exception as e:
        logger.error(f"Error extracting study dates: {str(e)}")

def scrape_nihr_trials():
    """Main function to scrape NIHR trials."""
    driver = None
    try:
        driver = setup_driver()
        trials = []
        
        logger.info(f"Navigating to {BASE_URL}")
        driver.get(BASE_URL)
        time.sleep(5)
        
        # Close cookie banner
        close_cookie_banner(driver)
        
        # Wait for initial content to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-v-204c41ad]"))
            )
        except Exception as e:
            logger.error(f"No trial articles found initially: {str(e)}")
            return
        
        # Scroll to load all trials
        total_trials = scroll_to_load_all_trials(driver)
        
        # Extract trial information from all loaded trials
        logger.info("Extracting trial information from all loaded trials...")
        trial_articles = driver.find_elements(By.CSS_SELECTOR, "article[data-v-204c41ad]")
        
        logger.info(f"Processing {len(trial_articles)} trial articles...")
        
        # First pass: extract basic information from all trials
        basic_trials = []
        for i, article in enumerate(trial_articles):
            try:
                trial_data = extract_trial_details(driver, article)
                if trial_data.get("title"):  # Only add if we got a title
                    basic_trials.append(trial_data)
                    logger.info(f"Extracted basic info for trial {i+1}: {trial_data['title']}")
                else:
                    logger.warning(f"Skipped trial {i+1} - no title found")
            except Exception as e:
                logger.error(f"Error processing trial {i+1}: {str(e)}")
                continue
        
        # Second pass: visit detail pages for additional information in batches
        batch_size = 10  # Process 10 trials in batches to avoid overwhelming the server
        total_batches = (len(basic_trials) + batch_size - 1) // batch_size  # Process all trials
        
        logger.info(f"Processing {len(basic_trials)} trials in {total_batches} batches of {batch_size}...")
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(basic_trials))
            batch_trials = basic_trials[start_idx:end_idx]
            
            logger.info(f"Processing batch {batch_num + 1}/{total_batches} (trials {start_idx + 1}-{end_idx})...")
            
            for i, trial_data in enumerate(batch_trials):
                try:
                    detailed_trial = extract_detailed_info(driver, trial_data)
                    trials.append(detailed_trial)
                    logger.info(f"  ✓ Processed trial {start_idx + i + 1}: {trial_data['title'][:50]}...")
                except Exception as e:
                    logger.error(f"Error getting detailed info for trial {start_idx + i + 1}: {str(e)}")
                    trials.append(trial_data)  # Add basic info even if detailed extraction fails
            
            # Add a delay between batches to be respectful to the server
            if batch_num < total_batches - 1:
                logger.info(f"Completed batch {batch_num + 1}/{total_batches}. Waiting 10 seconds before next batch...")
                time.sleep(10)
        
        # Save to JSON file
        output_file = "nihr_clinical_trials.json"
        with open(output_file, "w", encoding='utf-8') as f:
            json.dump(trials, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully scraped {len(trials)} NIHR trials and saved to {output_file}")
        
    except Exception as e:
        logger.error(f"An error occurred during scraping: {str(e)}")
        if driver:
            logger.error("Page source at time of error:")
            logger.error(driver.page_source[:1000])
    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver closed")

if __name__ == "__main__":
    scrape_nihr_trials() 