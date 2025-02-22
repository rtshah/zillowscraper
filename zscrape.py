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
        "location": "Houston, TX 77030",
        "properties": []
    }
    
    try:
        print("Starting the scraping process...")
        
        url = f"https://www.zillow.com/houston-tx-{zip_code}/rentals/"
        print(f"Navigating to rental listings...")
        driver.get(url)
        
        time.sleep(5)
        
        print("Waiting for rental property cards to load...")
        
        selectors = [
            "article[data-test='property-card']",
            "[data-test='property-card']"
        ]
        
        found_cards = False
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
        
        if not found_cards:
            print("Could not find rental property cards with any known selector")
            return scraped_data
        
        print(f"Found {len(property_cards)} rental properties")
        
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
                    ".StyledPropertyCardDataArea-c11n-8-84-3__sc-yipmu-0 div:nth-child(2)",
                    ".property-card-data",
                    "[data-test='property-card-details']"
                ]
                
                image_selectors = [
                    "img.StyledPropertyCardPhoto-c11n-8-84-3__sc-orx8zx-0",
                    "img[data-test='property-card-img']",
                    "img.property-card-img",
                    ".property-card-primary-photo img"
                ]
                
                property_data = {
                    "id": index,
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
                
                for selector in details_selectors:
                    try:
                        details_text = card.find_element(By.CSS_SELECTOR, selector).text
                        property_data["details"] = details_text
                        
                        details_lower = details_text.lower()
                        
                        if "bd" in details_lower:
                            beds = details_lower.split("bd")[0].strip().split()[-1]
                            try:
                                property_data["beds"] = float(beds.replace("+", ""))
                            except:
                                pass
                        
                        if "ba" in details_lower:
                            baths = details_lower.split("ba")[0].split()[-1]
                            try:
                                property_data["baths"] = float(baths.replace("+", ""))
                            except:
                                pass
                        
                        if "sqft" in details_lower:
                            sqft = details_lower.split("sqft")[0].strip().split()[-1]
                            try:
                                property_data["sqft"] = int(sqft.replace(",", ""))
                            except:
                                pass
                        
                        property_types = ["apartment", "house", "condo", "townhouse"]
                        for ptype in property_types:
                            if ptype in details_lower:
                                property_data["property_type"] = ptype
                                break
                        
                        break
                    except:
                        continue
                
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
                
                print(f"\nRental Property {index}:")
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
                print(f"Error extracting rental card {index} data: {e}")
                continue
    
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
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"zillow_rentals_{timestamp}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(scraped_data, f, indent=2)
            print(f"\nData saved to {filename}")
        except Exception as e:
            print(f"Error saving data to JSON: {e}")
        
        return scraped_data

if __name__ == "__main__":
    scrape_zillow("77030")