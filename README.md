# 📧 Email Finder Pro

A comprehensive email extraction and contact discovery tool with multiple search methods and AI-powered research capabilities.

## 🚀 Features

### 🔍 Dual Search Methods
- **AI-Powered Company Research**: Uses Perplexity AI via OpenRouter to find real leadership contacts
- **Direct Website Scraping**: Extract email addresses directly from any website

### 🛡️ Security & Privacy
- Secure API key handling with environment variables
- GDPR compliance considerations
- Rate limiting and respectful scraping

### 📊 Data Export
- CSV download functionality
- Clipboard copy support
- Structured data with source citations

## 🛠️ Setup

### Prerequisites
- Python 3.11+
- Chrome browser (for Selenium)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd email-finder
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file:
   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   RATE_LIMIT_DELAY=2
   MAX_RETRIES=3
   ```

4. **Get your OpenRouter API key**
   - Visit [OpenRouter.ai](https://openrouter.ai)
   - Sign up and get your API key
   - Add it to your `.env` file

## 🎯 Usage

### Method 1: AI Company Research
```bash
streamlit run company_lookup_app.py
```
- Enter company name, website, and country
- AI searches for real leadership contacts
- Get structured results with LinkedIn profiles and emails

### Method 2: Direct Website Scraping
```bash
streamlit run extractor.py
```
- Enter any website URL
- Extract all visible email addresses
- Download results as CSV

### Development Environment
Use the included DevContainer for consistent development:
```bash
# In VS Code with Dev Containers extension
# Command Palette > "Dev Containers: Reopen in Container"
```

## 📁 Project Structure

```
email-finder/
├── .devcontainer/
│   └── devcontainer.json          # Development environment config
├── .env                           # Environment variables (create this)
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── company_lookup_app.py          # AI-powered company research
├── extractor.py                   # Website email scraper
└── config/
    └── settings.py                # Configuration management
```

## ⚖️ Legal & Ethical Considerations

### GDPR Compliance
- Only collect publicly available information
- Respect robots.txt and website terms
- Provide data deletion capabilities
- Document data sources

### Rate Limiting
- Built-in delays between requests
- Respectful scraping practices
- API rate limit handling

### Data Usage
- Use extracted data responsibly
- Verify accuracy before outreach
- Respect opt-out requests

## 🔧 Configuration

### API Models
- **Recommended**: `perplexity/llama-3-sonar-large-online`
- **Fallback**: Any OpenRouter model with web access

### Scraping Settings
- **Delay**: 2 seconds between requests
- **Timeout**: 10 seconds per page
- **Retries**: 3 attempts max

## 🐛 Troubleshooting

### Common Issues

**Chrome Driver Issues**
```bash
# Update Chrome and reinstall webdriver-manager
pip install --upgrade webdriver-manager
```

**API Rate Limits**
- Check your OpenRouter usage limits
- Increase `RATE_LIMIT_DELAY` in .env

**No Emails Found**
- Try different search terms
- Check if the website blocks scraping
- Use the AI research method instead

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is for educational and research purposes. Ensure compliance with applicable laws and website terms of service.

## 🆘 Support

- Check the troubleshooting section
- Review OpenRouter documentation
- Create an issue for bugs or feature requests

---

**⚠️ Disclaimer**: Always respect website terms of service, robots.txt files, and applicable privacy laws when scraping data.
