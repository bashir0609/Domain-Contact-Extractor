import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv
import requests
import os
import re
import pandas as pd

def extract_emails(url):
    driver = webdriver.Chrome()
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    emails = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and (href.startswith('mailto:') or re.search(r'@', href)):
            emails.append(href)
    driver.quit()
    return emails

def main():
    url = st.text_input("Enter the website URL")
    if url:
        emails = extract_emails(url)
        df = pd.DataFrame({'Email': emails})
        st.write(df.to_string(index=False))
        st.download_button("Download CSV", data=df.to_csv(index=False), file_name='emails.csv')

if __name__ == "__main__":
    st.title("Email Scraper")
    main()
