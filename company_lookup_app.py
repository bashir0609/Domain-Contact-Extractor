import streamlit as st
import os
import requests
import pandas as pd
import logging
import time
import re
from datetime import datetime
from typing import Optional, List, Tuple, Dict
from dotenv import load_dotenv
from io import StringIO
import validators

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Config:
    """Configuration management"""
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.rate_limit_delay = float(os.getenv("RATE_LIMIT_DELAY", "2"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.default_model = "perplexity/llama-3-sonar-large-online"

class OpenRouterClient:
    """OpenRouter API client with error handling and rate limiting"""
    
    def __init__(self, api_key: str, rate_limit_delay: float = 2):
        self.api_key = api_key
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        
    def _wait_for_rate_limit(self):
        """Implement rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def get_available_models(self) -> List[str]:
        """Get available models from OpenRouter"""
        try:
            self._wait_for_rate_limit()
            resp = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            resp.raise_for_status()
            models = resp.json()["data"]
            return [model["id"] for model in models 
                   if "perplexity" in model["id"].lower() or "online" in model["id"].lower()]
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching models: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching models: {e}")
            return []
    
    def query_model(self, model: str, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Query OpenRouter with retry logic"""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 2000
        }
        
        for attempt in range(max_retries):
            try:
                self._wait_for_rate_limit()
                response = requests.post(url, headers=headers, json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()["choices"][0]["message"]["content"]
                    logger.info(f"Successful API call on attempt {attempt + 1}")
                    return result
                elif response.status_code == 429:  # Rate limited
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"Rate limited, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API error {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        return None

class DataProcessor:
    """Data processing utilities"""
    
    @staticmethod
    def parse_markdown_table(text: str) -> Optional[pd.DataFrame]:
        """Parse markdown table from AI response"""
        try:
            lines = text.split("\n")
            table_lines = [line for line in lines if "|" in line and "---" not in line]
            
            if len(table_lines) < 2:
                return None
                
            # Extract headers
            headers = [cell.strip() for cell in table_lines[0].split("|") if cell.strip()]
            if not headers:
                return None
            
            # Extract rows
            rows = []
            for line in table_lines[1:]:
                row = [cell.strip() for cell in line.split("|") if cell.strip()]
                if len(row) == len(headers):  # Only include complete rows
                    rows.append(row)
            
            if not rows:
                return None
                
            return pd.DataFrame(rows, columns=headers)
        except Exception as e:
            logger.error(f"Error parsing markdown table: {e}")
            return None
    
    @staticmethod
    def extract_citations(text: str) -> List[Tuple[str, str]]:
        """Extract citations from text"""
        pattern = r"\[([^\]]+)\]\((https?://[^\)]+)\)"
        return re.findall(pattern, text)
    
    @staticmethod
    def validate_company_data(company: str, website: str, country: str) -> Tuple[bool, str]:
        """Validate input data"""
        if not company or len(company.strip()) < 2:
            return False, "Company name must be at least 2 characters"
        
        if not website:
            return False, "Website URL is required"
            
        # Add protocol if missing
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
            
        if not validators.url(website):
            return False, "Invalid website URL format"
        
        if not country or len(country.strip()) < 2:
            return False, "Country must be at least 2 characters"
            
        return True, ""

def create_search_prompt(company: str, website: str, country: str) -> str:
    """Create optimized search prompt"""
    domain = website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
    
    return f"""
You are a professional business research assistant with web browsing capabilities.

**TASK**: Find verified contact information for key executives at {company} (website: {website}), located in {country}.

**SEARCH STRATEGY**:
1. Check the company's official website team/about pages
2. Search LinkedIn for current employees with leadership titles
3. Look for recent press releases or news articles
4. Check business directories and professional networks

**REQUIREMENTS**:

**OUTPUT FORMAT**: Return a clean markdown table with these exact columns:
| Name | Role | LinkedIn URL | Email | General Company Contact |

**DATA QUALITY RULES**:
- Only include individuals you can verify are current employees
- For emails: Use confirmed addresses or educated guesses based on company domain patterns
- Mark guessed emails with "(estimated)" 
- Include general company contact info when available
- Leave fields blank if no reliable information is found

**SOURCES**: After the table, provide a "Sources" section with clickable links to all references used.

**EXAMPLE OUTPUT**:
| Name | Role | LinkedIn URL | Email | General Company Contact |
|------|------|--------------|-------|-------|------------------------|
| Jane Smith | CEO | https://www.linkedin.com/in/janesmith | j.smith@{domain} | | info@{domain} |
| John Doe | CTO | https://www.linkedin.com/in/johndoe | john.doe@{domain}| | |

**Sources:**
- [Company Team Page](https://{domain}/team)
- [LinkedIn: Jane Smith](https://www.linkedin.com/in/janesmith)

**IMPORTANT**: 
- Focus on C-level executives, directors, and department heads
- Verify current employment status
- Prioritize recent and authoritative sources
- If no contacts found, explain your search process

Begin your research now for {company}.
"""

def main():
    # App configuration
    st.set_page_config(
        page_title="Company Contact Finder Pro",
        page_icon="📇",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize configuration
    config = Config()
    
    # Header
    st.title("📇 Company Contact Finder Pro")
    st.markdown("*AI-powered professional contact discovery with real-time web research*")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # API Key handling
        api_key = config.api_key
        if not api_key:
            api_key = st.text_input("🔐 OpenRouter API Key", type="password", 
                                   help="Get your key from openrouter.ai")
            if not api_key:
                st.error("API key required to continue")
                st.stop()
        else:
            st.success("✅ API key loaded from environment")
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            rate_limit = st.slider("Rate Limit (seconds)", 1, 10, int(config.rate_limit_delay))
            max_retries = st.slider("Max Retries", 1, 5, config.max_retries)
    
    # Initialize client
    client = OpenRouterClient(api_key, rate_limit)
    
    # Get available models
    with st.spinner("Loading available models..."):
        models = client.get_available_models()
    
    if not models:
        st.error("❌ No models available. Please check your API key.")
        st.stop()
    
    # Model selection
    preferred_model = config.default_model
    default_index = models.index(preferred_model) if preferred_model in models else 0
    
    model = st.selectbox(
        "🧠 AI Model", 
        models, 
        index=default_index,
        help="Perplexity models provide the best web search capabilities"
    )
    
    # Main input form
    st.header("🔍 Company Research")
    
    col1, col2 = st.columns(2)
    
    with col1:
        company = st.text_input(
            "🏢 Company Name *", 
            placeholder="e.g., Microsoft, Tesla, OpenAI",
            help="Enter the exact company name"
        )
        
        website = st.text_input(
            "🌐 Company Website *", 
            placeholder="e.g., microsoft.com, tesla.com",
            help="Main company website (with or without https://)"
        )
    
    with col2:
        country = st.text_input(
            "📍 Country/Region *", 
            value="United States",
            help="Primary company location"
        )
        
        search_depth = st.selectbox(
            "🔎 Search Depth",
            ["Standard", "Deep Research"],
            help="Deep research may take longer but provides more comprehensive results"
        )
    
    # Search button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        search_button = st.button(
            "🚀 Find Leadership Contacts", 
            type="primary",
            use_container_width=True
        )
    
    # Process search
    if search_button:
        # Validate inputs
        is_valid, error_msg = DataProcessor.validate_company_data(company, website, country)
        if not is_valid:
            st.error(f"❌ {error_msg}")
            return
        
        # Show search progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Update progress
            progress_bar.progress(25)
            status_text.text("🔍 Generating search strategy...")
            
            # Create prompt
            prompt = create_search_prompt(company, website, country)
            
            # Execute search
            progress_bar.progress(50)
            status_text.text("🌐 Searching the web for contacts...")
            
            result = client.query_model(model, prompt, max_retries)
            
            progress_bar.progress(75)
            status_text.text("📊 Processing results...")
            
            if not result:
                st.error("❌ Failed to get results from AI. Please try again.")
                return
            
            # Display results
            progress_bar.progress(100)
            status_text.text("✅ Search completed!")
            
            st.header("📋 Research Results")
            
            # Show raw results
            with st.expander("📄 Full AI Response", expanded=True):
                st.markdown(result)
            
            # Parse and display structured data
            df = DataProcessor.parse_markdown_table(result)
            
            if df is not None and not df.empty:
                st.subheader("📊 Structured Data")
                st.dataframe(df, use_container_width=True)
                
                # Export options
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    csv_data = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "⬇️ Download CSV",
                        data=csv_data,
                        file_name=f"{company.lower().replace(' ', '_')}_contacts_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # Copy to clipboard functionality
                    st.text_area(
                        "📋 Copy Data",
                        df.to_csv(index=False),
                        height=150,
                        help="Select all and copy to clipboard"
                    )
            
            # Show citations
            citations = DataProcessor.extract_citations(result)
            if citations:
                st.subheader("📚 Sources & References")
                for i, (name, url) in enumerate(citations, 1):
                    st.markdown(f"{i}. [{name}]({url})")
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            st.error(f"❌ An error occurred: {str(e)}")
            progress_bar.empty()
            status_text.empty()
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("⚖️ **Legal**: Use responsibly and respect privacy laws")
    
    with col2:
        st.caption("🔒 **Privacy**: Data is not stored permanently")
    
    with col3:
        st.caption("🎯 **Accuracy**: Always verify contact information")

if __name__ == "__main__":
    main()
