import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import random
import json
from datetime import datetime
import os

def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    ]
    return random.choice(user_agents)

def inject_jquery(driver):
    jquery_js = """
    if (typeof jQuery == 'undefined') {
        var script = document.createElement('script');
        script.src = 'https://code.jquery.com/jquery-3.6.0.min.js';
        document.getElementsByTagName('head')[0].appendChild(script);
    }
    """
    try:
        driver.execute_script(jquery_js)
        time.sleep(1)  
    except:
        pass

def setup_driver():
    options = uc.ChromeOptions()
    
    options.add_argument("--start-maximized") 
    
    driver = uc.Chrome(
        options=options,
        driver_executable_path=None,  
        suppress_welcome=True, 
        headless=False, 
        use_subprocess=True, 
    )
    return driver

def wait_for_manual_verification():
    print("\nWaiting 30 seconds for you to complete any verification...")
    print("If you see a verification page, please complete it now.")
    time.sleep(30)
    print("Continuing with scraping...")

def scrape_zillow(zip_code):
    driver = setup_driver()
    wait = WebDriverWait(driver, 20)
    scraped_data = {
        "timestamp": datetime.now().isoformat(),
        "location": f"Houston, TX {zip_code}",
        "properties": []
    }
    
    try:
        page = 1
        while True:  # Continue until we run out of pages
            print(f"\nScraping page {page}...")
            
            # Construct URL with pagination
            if page == 1:
                url = f"https://www.zillow.com/houston-tx-{zip_code}/rentals/"
            else:
                url = f"https://www.zillow.com/houston-tx-{zip_code}/rentals/{page}_p/"
            
            print(f"Navigating to: {url}")
            driver.get(url)
            
            # Wait for page to load
            time.sleep(5)
            
            print("Waiting for rental property cards to load...")
            
            # Check if we've reached the end of listings
            try:
                no_results = driver.find_elements(By.CSS_SELECTOR, ".zero-results-message")
                if no_results:
                    print("No more listings found.")
                    break
            except:
                pass
            
            selectors = [
                "article[data-test='property-card']",
                "[data-test='property-card']"
            ]
            
            found_cards = False
            property_cards = []
            
            for selector in selectors:
                try:
                    first_card = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    property_cards = driver.find_elements(By.CSS_SELECTOR, selector)
                    found_cards = True
                    print(f"Found cards using selector: {selector}")
                    break
                except:
                    continue
            
            if not found_cards or len(property_cards) == 0:
                print("No property cards found on this page. Ending search.")
                break
            
            print(f"Found {len(property_cards)} rental properties on page {page}")
            
            for index, card in enumerate(property_cards, 1):
                try:
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", card)
                    time.sleep(random.uniform(1, 2))
                    
                    price_selectors = [
                        "[data-test='property-card-price']",
                        ".list-card-price",
                        "span[data-test='property-card-price']",
                        ".StyledPropertyCardDataArea-c11n-8-84-3__sc-yipmu-0 span"
                    ]
                    
                    address_selectors = [
                        "address",
                        ".list-card-addr",
                        "[data-test='property-card-addr']",
                        ".StyledPropertyCardDataArea-c11n-8-84-3__sc-yipmu-0 address"
                    ]
                    
                    details_selectors = [
                        "[data-test='property-card-details']",
                        "[data-test='beds-baths-sqft']",
                        "[data-test='beds-baths-sqft-info']",
                        ".property-card-data",
                        ".list-card-details"
                    ]
                    
                    image_selectors = [
                        "img.StyledPropertyCardPhoto-c11n-8-84-3__sc-orx8zx-0",
                        "img[data-test='property-card-img']",
                        "img.property-card-img",
                        ".property-card-primary-photo img"
                    ]
                    
                    property_data = {
                        "id": len(scraped_data["properties"]) + 1,  # Global ID across all pages
                        "page": page,
                        "price": "Price not found",
                        "address": "Address not found",
                        "details": "Details not found",
                        "image_url": "Image URL not found",
                        "beds": None,
                        "baths": None,
                        "sqft": None,
                        "property_type": None,
                        "url": None
                    }
                    
                    for selector in price_selectors:
                        try:
                            property_data["price"] = card.find_element(By.CSS_SELECTOR, selector).text
                            break
                        except:
                            continue
                    
                    for selector in address_selectors:
                        try:
                            property_data["address"] = card.find_element(By.CSS_SELECTOR, selector).text
                            break
                        except:
                            continue
                    
                    # Extract details text from multiple elements if needed
                    details_text = ""
                    for selector in details_selectors:
                        try:
                            elements = card.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                details_text += element.text + " "
                            if details_text.strip():
                                break
                        except:
                            continue
                    
                    property_data["details"] = details_text.strip()
                    
                    # Parse the details text
                    if details_text:
                        details_lower = details_text.lower()
                        
                        # Extract beds (handle both "Studio" and numeric values)
                        if "studio" in details_lower:
                            property_data["beds"] = 0
                        elif "bd" in details_lower:
                            try:
                                beds_text = details_lower.split("bd")[0].strip().split()[-1]
                                property_data["beds"] = float(beds_text.replace("+", ""))
                            except:
                                pass
                        
                        # Extract baths
                        if "ba" in details_lower:
                            try:
                                # Look for patterns like "2 ba" or "2.5 ba"
                                bath_text = details_lower.split("ba")[0].strip()
                                # Extract the last number before "ba"
                                numbers = [float(s.replace("+", "")) for s in bath_text.split() if s.replace(".", "").replace("+", "").isdigit()]
                                if numbers:
                                    # Take the last number that's reasonable for baths (less than 10)
                                    reasonable_baths = [n for n in numbers if n < 10]
                                    if reasonable_baths:
                                        property_data["baths"] = reasonable_baths[-1]
                            except:
                                pass
                        
                        # Extract sqft
                        if "sqft" in details_lower:
                            try:
                                # Look for patterns like "1,234 sqft" or "1234 sqft"
                                sqft_text = details_lower.split("sqft")[0].strip()
                                # Extract the last number before "sqft"
                                numbers = [int(s.replace(",", "").replace("+", "")) 
                                         for s in sqft_text.split() 
                                         if s.replace(",", "").replace("+", "").isdigit()]
                                if numbers:
                                    # Take the last number that's reasonable for sqft (between 100 and 10000)
                                    reasonable_sqft = [n for n in numbers if 100 <= n <= 10000]
                                    if reasonable_sqft:
                                        property_data["sqft"] = reasonable_sqft[-1]
                            except:
                                pass
                        
                        # Extract property type (improved detection)
                        property_types = {
                            "apartment": ["apartment", "apt", "unit"],
                            "house": ["house", "home", "single family"],
                            "condo": ["condo", "condominium"],
                            "townhouse": ["townhouse", "townhome", "town house"]
                        }
                        
                        for ptype, keywords in property_types.items():
                            if any(keyword in details_lower for keyword in keywords):
                                property_data["property_type"] = ptype
                                break
                        
                        # If no property type found but it's a rental listing, assume apartment
                        if not property_data["property_type"] and "for rent" in details_lower:
                            property_data["property_type"] = "apartment"
                    
                    for selector in image_selectors:
                        try:
                            img_element = card.find_element(By.CSS_SELECTOR, selector)
                            image_url = img_element.get_attribute('src')
                            if not image_url:
                                image_url = img_element.get_attribute('data-src')
                            if image_url:
                                property_data["image_url"] = image_url
                                break
                        except:
                            continue
                    
                    try:
                        url_element = card.find_element(By.CSS_SELECTOR, "a")
                        property_data["url"] = url_element.get_attribute("href")
                    except:
                        pass
                    
                    scraped_data["properties"].append(property_data)
                    
                    print(f"\nRental Property {property_data['id']} (Page {page}):")
                    print(f"Monthly Rent: {property_data['price']}")
                    print(f"Address: {property_data['address']}")
                    print(f"Details: {property_data['details']}")
                    print(f"Beds: {property_data['beds']}")
                    print(f"Baths: {property_data['baths']}")
                    print(f"Square Feet: {property_data['sqft']}")
                    print(f"Property Type: {property_data['property_type']}")
                    print(f"Image URL: {property_data['image_url']}")
                    print(f"Listing URL: {property_data['url']}")
                    print("-" * 50)
                    
                    time.sleep(random.uniform(1, 2))
                
                except Exception as e:
                    print(f"Error extracting rental card {index} on page {page}: {e}")
                    continue
            
            # Save progress after each page
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"zillow_rentals_{timestamp}_progress.json"
            try:
                with open(filename, 'w') as f:
                    json.dump(scraped_data, f, indent=2)
                print(f"\nProgress saved to {filename}")
            except Exception as e:
                print(f"Error saving progress to JSON: {e}")
            
            # Check if there's a next page button
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "a[title='Next page']")
                if not next_button.is_enabled():
                    print("Reached the last page.")
                    break
            except:
                print("No more pages found.")
                break
            
            page += 1
            # Add a delay between pages to avoid rate limiting
            time.sleep(random.uniform(3, 5))
    
    except TimeoutException:
        print("Timeout waiting for page to load. This might mean Zillow is blocking the request.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Closing browser...")
        try:
            driver.quit()
        except:
            pass
        
        # Save final results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"zillow_rentals_{timestamp}_final.json"
        try:
            with open(filename, 'w') as f:
                json.dump(scraped_data, f, indent=2)
            print(f"\nFinal data saved to {filename}")
        except Exception as e:
            print(f"Error saving data to JSON: {e}")
        
        return scraped_data

if __name__ == "__main__":
    scrape_zillow("77030")