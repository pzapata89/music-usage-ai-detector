# Music Usage AI Detector 🎵

A powerful Python application that helps organizations detect possible uses of songs on the internet using AI-powered analysis.

## Features

- **YouTube Search**: Search YouTube videos using the YouTube Data API
- **Web Search**: Search Google results using SerpAPI
- **AI Classification**: Automatically classify results into usage categories
- **Beautiful UI**: Modern Streamlit interface with responsive design
- **Comprehensive Reports**: Generate detailed usage reports with insights

## AI Classification Categories

The application uses OpenAI to classify search results into four categories:

1. **Possible Song Usage** - Direct use of the song in content
2. **Cover** - Someone covering or performing the song
3. **Promotional Usage** - Using song for promotion or marketing
4. **Reference Only** - Mentioning the song but not using it

## Project Structure

```
music_usage_detector/
├── app.py                 # Main Streamlit application
├── youtube_search.py      # YouTube API integration
├── web_search.py          # SerpAPI integration
├── ai_analysis.py         # AI classification module
├── config.py              # Configuration and API key management
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── .env                   # Environment variables (create this)
```

## Installation

### Prerequisites

- Python 3.10 or higher
- API keys for YouTube, SerpAPI, and OpenAI

### Step 1: Clone or Download

```bash
# If using git
git clone <repository-url>
cd music_usage_detector

# Or download and extract the files
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### Step 1: Get API Keys

1. **YouTube Data API Key**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable YouTube Data API v3
   - Create credentials (API Key)

2. **SerpAPI Key**:
   - Sign up at [SerpAPI](https://serpapi.com/)
   - Get your API key from the dashboard

3. **OpenAI API Key**:
   - Sign up at [OpenAI](https://platform.openai.com/)
   - Get your API key from the API keys section

### Step 2: Set Up Environment Variables

Create a `.env` file in the project root:

```env
YOUTUBE_API_KEY=your_youtube_api_key_here
SERPAPI_API_KEY=your_serpapi_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

**Important**: Never commit your `.env` file to version control. Add it to `.gitignore`:

```gitignore
.env
venv/
__pycache__/
*.pyc
```

## Usage

### Running the Application

```bash
streamlit run app.py
```

The application will open in your web browser at `http://localhost:8501`

### Using the Interface

1. **Enter Song Details**:
   - Type the song name in the "Song Name" field
   - Type the artist name in the "Artist Name" field

2. **Search**:
   - Click the "Search Usage" button
   - Wait for the search and AI analysis to complete

3. **Review Results**:
   - View the analysis summary with metrics
   - Browse YouTube results with AI classifications
   - Explore web results with detailed categorization

4. **Interpret Results**:
   - Each result shows the title, link, description, and AI classification
   - Confidence scores indicate how certain the AI is about the classification
   - The summary provides insights about overall usage patterns

## API Usage Limits

- **YouTube Data API**: 10,000 units per day (free tier)
- **SerpAPI**: 100 searches per month (free tier)
- **OpenAI API**: Usage-based pricing (check current rates)

## Troubleshooting

### Common Issues

1. **API Key Errors**:
   - Ensure all API keys are correctly set in the `.env` file
   - Check that API keys are valid and active

2. **Import Errors**:
   - Make sure you've installed all dependencies
   - Activate the virtual environment

3. **No Results Found**:
   - Try different search terms
   - Check if song/artist names are spelled correctly

4. **Slow Performance**:
   - AI analysis may take time depending on result count
   - Consider reducing the number of search results

### Debug Mode

To enable detailed logging, modify the logging level in the modules:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Development

### Adding New Features

The modular structure makes it easy to extend:

1. **New Search Sources**: Add new searcher classes following the pattern in `youtube_search.py`
2. **Custom Classifications**: Modify the categories in `ai_analysis.py`
3. **UI Enhancements**: Update the Streamlit interface in `app.py`

### Testing

```bash
# Run basic functionality test
python -c "from config import config; print('API keys loaded successfully')"
```

## Security Considerations

- Never expose API keys in client-side code
- Use environment variables for sensitive data
- Regularly rotate API keys
- Monitor API usage for unusual activity

## License

This project is provided as-is for educational and development purposes.

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Verify API key configurations
3. Review the logs for detailed error messages

---

**Made with ❤️ using Streamlit, YouTube Data API, SerpAPI, and OpenAI**
