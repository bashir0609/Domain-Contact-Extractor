import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import validators

def configure_selenium():
    """Configure Selenium WebDriver with headless options"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=chrome_options)

def extract_emails(url):
    """Extract emails from a webpage with improved validation"""
    try:
        driver = configure_selenium()
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        
        # Scroll to load dynamic content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Allow time for dynamic content
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        emails = set()  # Using set to avoid duplicates
        
        # Email regex pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Find emails in href attributes
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if href.startswith('mailto:'):
                email = href[7:]
                if validators.email(email):
                    emails.add(email)
        
        # Find emails in text content
        text_emails = re.findall(email_pattern, soup.get_text())
        for email in text_emails:
            if validators.email(email):
                emails.add(email)
                
        driver.quit()
        return sorted(emails)
    
    except Exception as e:
        st.error(f"Error scraping {url}: {str(e)}")
        return []

def main():
    st.title("📧 Advanced Email Scraper")
    st.markdown("Extract email addresses from any website")
    
    with st.form("scraper_form"):
        url = st.text_input("Enter website URL (include http:// or https://)", 
                           placeholder="https://example.com")
        submitted = st.form_submit_button("Extract Emails")
    
    if submitted:
        if not url:
            st.warning("Please enter a valid URL")
            return
            
        if not validators.url(url):
            st.error("Invalid URL format. Please include http:// or https://")
            return
            
        with st.spinner(f"Scraping {url}..."):
            emails = extract_emails(url)
            
        if emails:
            st.success(f"Found {len(emails)} email addresses")
            df = pd.DataFrame({'Email': emails})
            
            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(df)
            with col2:
                st.download_button(
                    label="Download as CSV",
                    data=df.to_csv(index=False),
                    file_name='extracted_emails.csv',
                    mime='text/csv'
                )
        else:
            st.warning("No email addresses found on this page")

if __name__ == "__main__":
    main()
