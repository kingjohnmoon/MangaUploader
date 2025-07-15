from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import json

class MangaUploader:
    def __init__(self, headless=False, cookies_path="cookies.json"):
        """
        Initialize the MangaUploader with Selenium WebDriver
        :param headless: Run browser in headless mode
        :param cookies_path: Path to save/load cookies for session persistence
        """
        self.headless = headless
        self.cookies_path = cookies_path
        self.driver = None
        self.wait = None
        self._setup_driver()

    def _setup_driver(self):
        """Setup Chrome WebDriver with options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize driver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 30)

    def save_cookies(self):
        """Save current cookies to file"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_path, 'w') as f:
                json.dump(cookies, f)
            print("Cookies saved successfully")
        except Exception as e:
            print(f"Error saving cookies: {e}")

    def load_cookies(self):
        """Load cookies from file"""
        try:
            if os.path.exists(self.cookies_path):
                with open(self.cookies_path, 'r') as f:
                    cookies = json.load(f)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
                print("Cookies loaded successfully")
                return True
        except Exception as e:
            print(f"Error loading cookies: {e}")
        return False

    def login_to_tiktok(self):
        """Navigate to TikTok and handle login"""
        try:
            self.driver.get("https://www.tiktok.com/upload")
            
            # Load cookies if available
            self.load_cookies()
            self.driver.refresh()
            
            # Check if already logged in
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='upload-icon']")))
                print("Already logged in!")
                return True
            except TimeoutException:
                print("Not logged in, please log in manually...")
                
            # Wait for manual login
            print("Please log in manually in the browser window...")
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='upload-icon']")))
            
            # Save cookies after successful login
            self.save_cookies()
            return True
            
        except TimeoutException:
            print("Login timeout or failed to find upload area")
            return False
        except Exception as e:
            print(f"Error during login: {e}")
            return False

    def upload_image(self, image_path, caption="", hashtags=None):
        """
        Upload an image to TikTok
        :param image_path: Path to the image file
        :param caption: Caption for the post
        :param hashtags: List of hashtags or string
        """
        try:
            # Ensure we're logged in and on upload page
            if not self.login_to_tiktok():
                return {"success": False, "error": "Login failed"}
            
            # Find and click upload button/area
            try:
                upload_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
                upload_input.send_keys(os.path.abspath(image_path))
            except TimeoutException:
                return {"success": False, "error": "Could not find upload input"}
            
            # Wait for upload to process
            print("Waiting for upload to process...")
            time.sleep(5)  # Give time for upload to start
            
            # Add caption and hashtags
            try:
                caption_input = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='caption-input'], [placeholder*='caption'], textarea")))
                caption_input.clear()
                
                # Normalize hashtags
                hashtags_str = self._normalize_hashtags(hashtags)
                full_caption = f"{caption} {hashtags_str}".strip()
                
                caption_input.send_keys(full_caption)
                print(f"Caption added: {full_caption}")
            except TimeoutException:
                print("Could not find caption input, continuing...")
            
            # Find and click publish button
            try:
                publish_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-e2e='publish-button'], button[data-e2e='publish-button']")))
                publish_button.click()
                print("Publish button clicked")
            except TimeoutException:
                return {"success": False, "error": "Could not find publish button"}
            
            # Wait for upload completion
            print("Waiting for upload to complete...")
            try:
                # Look for success indicators
                self.wait.until(EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='upload-success']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".upload-success")),
                    EC.url_contains("foryou")  # Sometimes redirects to home page
                ))
                print("Upload completed successfully!")
                return {"success": True, "message": "Upload completed"}
            except TimeoutException:
                return {"success": False, "error": "Upload timeout - may have failed"}
                
        except Exception as e:
            return {"success": False, "error": f"Upload failed: {str(e)}"}

    def _normalize_hashtags(self, hashtags):
        """Convert hashtags to proper format"""
        if not hashtags:
            return ""
        if isinstance(hashtags, list):
            return " ".join([f"#{tag.lstrip('#')}" for tag in hashtags])
        if isinstance(hashtags, str):
            tags = hashtags.split()
            return " ".join([f"#{tag.lstrip('#')}" for tag in tags])
        return ""

    def upload_folder(self, folder_path, caption_template="", hashtags=None):
        """
        Upload all images from a folder
        :param folder_path: Path to folder containing images
        :param caption_template: Template for captions
        :param hashtags: Hashtags to use for all uploads
        """
        if not os.path.exists(folder_path):
            print(f"Folder {folder_path} does not exist")
            return
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        results = []
        
        for filename in os.listdir(folder_path):
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                image_path = os.path.join(folder_path, filename)
                caption = f"{caption_template} - {filename}" if caption_template else filename
                
                print(f"Uploading: {filename}")
                result = self.upload_image(image_path, caption, hashtags)
                results.append({"file": filename, "result": result})
                
                if result["success"]:
                    print(f"✓ Successfully uploaded {filename}")
                else:
                    print(f"✗ Failed to upload {filename}: {result.get('error', 'Unknown error')}")
                
                # Add delay between uploads to avoid rate limiting
                time.sleep(30)  # 30 second delay
        
        return results

    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
            print("Browser closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

# Example usage
if __name__ == "__main__":
    # Example: Upload a single image
    with MangaUploader() as uploader:
        result = uploader.upload_image(
            "path/to/image.jpg", 
            "Check out this manga page!", 
            ["#manga", "#anime", "#otaku"]
        )
        print(result)
    
    # Example: Upload all images from downloads folder
    # with MangaUploader() as uploader:
    #     results = uploader.upload_folder(
    #         "downloads", 
    #         "Amazing manga content", 
    #         ["#manga", "#anime"]
    #     )
    #     print(f"Uploaded {len([r for r in results if r['result']['success']])} files successfully")