import streamlit as st
import logging
import time
import re
import csv
from datetime import datetime
from typing import List, Set, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import pandas as pd
import validators
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailExtractor:
    """Advanced email extraction with multiple methods"""
    
    def __init__(self):
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            re.IGNORECASE
        )
        self.excluded_domains = {
            'example.com', 'test.com', 'domain.com', 'yoursite.com',
            'sentry.io', 'google.com', 'facebook.com', 'twitter.com',
            'linkedin.com', 'instagram.com', 'youtube.com', 'wordpress.com'
        }
        
    def _is_valid_email(self, email: str) -> bool:
        """Validate email with additional filters"""
        try:
            if not validators.email(email):
                return False
            
            domain = email.split('@')[1].lower()
            
            # Filter out common excluded domains
            if domain in self.excluded_domains:
                return False
            
            # Filter out obvious fake emails
            fake_patterns = [
                r'noreply', r'no-reply', r'donotreply', r'test@',
                r'admin@example', r'user@example', r'contact@example'
            ]
            
            for pattern in fake_patterns:
                if re.search(pattern, email.lower()):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _configure_selenium(self) -> webdriver.Chrome:
        """Configure Selenium WebDriver with optimized options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            driver = webdriver.Chrome(
                ChromeDriverManager().install(),
                options=chrome_options
            )
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            raise
    
    def extract_with_requests(self, url: str) -> Set[str]:
        """Extract emails using requests (faster, but limited)"""
        emails = set()
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract from mailto links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('mailto:'):
                    email = href[7:].split('?')[0]  # Remove query parameters
                    if self._is_valid_email(email):
                        emails.add(email.lower())
            
            # Extract from text content
            text_content = soup.get_text()
            found_emails = self.email_pattern.findall(text_content)
            
            for email in found_emails:
                if self._is_valid_email(email):
                    emails.add(email.lower())
            
            logger.info(f"Requests method found {len(emails)} emails")
            return emails
            
        except Exception as e:
            logger.warning(f"Requests extraction failed: {e}")
            return set()
    
    def extract_with_selenium(self, url: str) -> Set[str]:
        """Extract emails using Selenium (more thorough)"""
        emails = set()
        driver = None
        
        try:
            driver = self._configure_selenium()
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            
            # Scroll to load dynamic content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Get page source and parse
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extract from mailto links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('mailto:'):
                    email = href[7:].split('?')[0]
                    if self._is_valid_email(email):
                        emails.add(email.lower())
            
            # Extract from text content
            text_content = soup.get_text()
            found_emails = self.email_pattern.findall(text_content)
            
            for email in found_emails:
                if self._is_valid_email(email):
                    emails.add(email.lower())
            
            # Look for hidden or dynamically loaded content
            try:
                # Check for contact forms or hidden sections
                contact_sections = driver.find_elements(By.CSS_SELECTOR, 
                    "[class*='contact'], [id*='contact'], [class*='email'], [id*='email']")
                
                for section in contact_sections:
                    section_text = section.text
                    section_emails = self.email_pattern.findall(section_text)
                    for email in section_emails:
                        if self._is_valid_email(email):
                            emails.add(email.lower())
            except Exception:
                pass
            
            logger.info(f"Selenium method found {len(emails)} emails")
            return emails
            
        except TimeoutException:
            logger.warning("Page load timeout")
            return set()
        except WebDriverException as e:
            logger.error(f"WebDriver error: {e}")
            return set()
        except Exception as e:
            logger.error(f"Selenium extraction failed: {e}")
            return set()
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
    
    def extract_from_sitemap(self, base_url: str) -> Set[str]:
        """Extract emails from sitemap URLs"""
        emails = set()
        
        try:
            # Try common sitemap locations
            sitemap_urls = [
                urljoin(base_url, 'sitemap.xml'),
                urljoin(base_url, 'sitemap_index.xml'),
                urljoin(base_url, 'sitemap.txt')
            ]
            
            for sitemap_url in sitemap_urls:
                try:
                    response = requests.get(sitemap_url, timeout=5)
                    if response.status_code == 200:
                        # Simple extraction from sitemap content
                        found_emails = self.email_pattern.findall(response.text)
                        for email in found_emails:
                            if self._is_valid_email(email):
                                emails.add(email.lower())
                        break
                except Exception:
                    continue
            
            return emails
            
        except Exception as e:
            logger.warning(f"Sitemap extraction failed: {e}")
            return set()

class EmailAnalyzer:
    """Analyze and categorize extracted emails"""
    
    @staticmethod
    def categorize_emails(emails: List[str]) -> Dict[str, List[str]]:
        """Categorize emails by type"""
        categories = {
            'general': [],
            'sales': [],
            'support': [],
            'info': [],
            'admin': [],
            'personal': []
        }
        
        patterns = {
            'sales': [r'sales', r'business', r'commercial'],
            'support': [r'support', r'help', r'service'],
            'info': [r'info', r'contact', r'hello'],
            'admin': [r'admin', r'webmaster', r'postmaster']
        }
        
        for email in emails:
            local_part = email.split('@')[0].lower()
            categorized = False
            
            for category, pattern_list in patterns.items():
                for pattern in pattern_list:
                    if re.search(pattern, local_part):
                        categories[category].append(email)
                        categorized = True
                        break
                if categorized:
                    break
            
            if not categorized:
                # Check if it looks like a personal email
                if '.' in local_part or len(local_part.split('.')) > 1:
                    categories['personal'].append(email)
                else:
                    categories['general'].append(email)
        
        return {k: v for k, v in categories.items() if v}  # Remove empty categories

def main():
    st.set_page_config(
        page_title="Email Extractor Pro",
        page_icon="📧",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📧 Email Extractor Pro")
    st.markdown("*Advanced email extraction with multiple methods and analysis*")
    
    # Sidebar settings
    with st.sidebar:
        st.header("⚙️ Extraction Settings")
        
        extraction_method = st.selectbox(
            "Extraction Method",
            ["Auto (Requests + Selenium)", "Requests Only (Fast)", "Selenium Only (Thorough)"],
            help="Auto tries requests first, then Selenium if needed"
        )
        
        include_sitemap = st.checkbox(
            "Include Sitemap Search",
            value=True,
            help="Also search sitemap.xml for additional emails"
        )
        
        categorize_results = st.checkbox(
            "Categorize Results",
            value=True,
            help="Group emails by type (sales, support, etc.)"
        )
        
        st.markdown("---")
        st.caption("💡 **Tips:**")
        st.caption("• Use 'Requests Only' for speed")
        st.caption("• Use 'Selenium Only' for JS-heavy sites")
        st.caption("• 'Auto' provides best coverage")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        url = st.text_input(
            "🌐 Website URL",
            placeholder="https://example.com",
            help="Enter the full URL including https://"
        )
    
    with col2:
        extract_button = st.button(
            "🚀 Extract Emails",
            type="primary",
            use_container_width=True
        )
    
    # URL validation
    if url and not validators.url(url):
        st.error("❌ Please enter a valid URL (including https://)")
        return
    
    # Main extraction logic
    if extract_button and url:
        extractor = EmailExtractor()
        all_emails = set()
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Method 1: Requests
            if extraction_method in ["Auto (Requests + Selenium)", "Requests Only (Fast)"]:
                status_text.text("🔍 Extracting with HTTP requests...")
                progress_bar.progress(25)
                
                requests_emails = extractor.extract_with_requests(url)
                all_emails.update(requests_emails)
                
                st.info(f"✅ Found {len(requests_emails)} emails with requests method")
            
            # Method 2: Selenium (if needed or requested)
            if extraction_method in ["Auto (Requests + Selenium)", "Selenium Only (Thorough)"]:
                # For auto mode, only use Selenium if requests found few emails
                should_use_selenium = (
                    extraction_method == "Selenium Only (Thorough)" or
                    (extraction_method == "Auto (Requests + Selenium)" and len(all_emails) < 3)
                )
                
                if should_use_selenium:
                    status_text.text("🌐 Extracting with browser automation...")
                    progress_bar.progress(50)
                    
                    selenium_emails = extractor.extract_with_selenium(url)
                    all_emails.update(selenium_emails)
                    
                    st.info(f"✅ Found {len(selenium_emails)} additional emails with Selenium")
            
            # Method 3: Sitemap
            if include_sitemap:
                status_text.text("🗺️ Searching sitemap...")
                progress_bar.progress(75)
                
                sitemap_emails = extractor.extract_from_sitemap(url)
                all_emails.update(sitemap_emails)
                
                if sitemap_emails:
                    st.info(f"✅ Found {len(sitemap_emails)} emails in sitemap")
            
            # Finalize results
            progress_bar.progress(100)
            status_text.text("✅ Extraction completed!")
            
            # Display results
            if all_emails:
                st.success(f"🎉 Found {len(all_emails)} unique email addresses")
                
                # Convert to sorted list
                email_list = sorted(list(all_emails))
                
                # Categorization
                if categorize_results:
                    analyzer = EmailAnalyzer()
                    categories = analyzer.categorize_emails(email_list)
                    
                    st.subheader("📊 Categorized Results")
                    
                    for category, emails in categories.items():
                        with st.expander(f"{category.title()} ({len(emails)} emails)", expanded=True):
                            for email in emails:
                                st.write(f"📧 {email}")
                else:
                    st.subheader("📧 All Email Addresses")
                    for email in email_list:
                        st.write(f"📧 {email}")
                
                # Create DataFrame for export
                if categorize_results and categories:
                    # Create a DataFrame with categories
                    export_data = []
                    for category, emails in categories.items():
                        for email in emails:
                            export_data.append({"Email": email, "Category": category.title()})
                    df = pd.DataFrame(export_data)
                else:
                    df = pd.DataFrame({"Email": email_list})
                
                # Export options
                st.subheader("📤 Export Options")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "⬇️ Download CSV",
                        data=csv_data,
                        file_name=f"emails_{urlparse(url).netloc}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    txt_data = '\n'.join(email_list).encode('utf-8')
                    st.download_button(
                        "⬇️ Download TXT",
                        data=txt_data,
                        file_name=f"emails_{urlparse(url).netloc}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain"
                    )
                
                with col3:
                    st.text_area(
                        "📋 Copy to Clipboard",
                        value='\n'.join(email_list),
                        height=100,
                        help="Select all and copy"
                    )
                
                # Statistics
                with st.expander("📈 Extraction Statistics"):
                    domain = urlparse(url).netloc
                    domain_emails = [e for e in email_list if domain.replace('www.', '') in e]
                    external_emails = [e for e in email_list if domain.replace('www.', '') not in e]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Emails", len(email_list))
                    with col2:
                        st.metric("Domain Emails", len(domain_emails))
                    with col3:
                        st.metric("External Emails", len(external_emails))
            
            else:
                st.warning("🔍 No email addresses found on this page.")
                st.info("💡 Try using 'Selenium Only' method or check if the site has a contact page.")
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            st.error(f"❌ An error occurred: {str(e)}")
            progress_bar.empty()
            status_text.empty()
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("⚖️ **Legal**: Respect robots.txt and terms of service")
    
    with col2:
        st.caption("🔒 **Privacy**: No data is stored or shared")
    
    with col3:
        st.caption("🎯 **Quality**: Results are filtered and validated")

if __name__ == "__main__":
    main()
