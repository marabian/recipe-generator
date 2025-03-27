# Streamlit Recipe Generator

A Streamlit web application that allows users to generate recipes based on ingredients using Gemini's text and image generation capabilities.

## Features

- **Recipe Generation**: Generate detailed recipes with step-by-step instructions and images
- **Recipe Collection**: Save and manage your favorite recipes
- **Ingredients & Preferences**: Manage your ingredients and set your culinary preferences
- **Settings**: Customize your experience with unit preferences and theme options

## Architecture

### Project Structure

```
recipe-generator/
├── app.py                  # Main application
├── requirements.txt        # Project dependencies
├── README.md               # Documentation
│   └── settings.py               # App settings page
├── services/               # Service layer
│   └── gemini_service.py   # Gemini API integration
└── prompts/                # System prompts
    └── recipe_prompts.py   # Recipe generation prompts
```

### Technical Details

- Multi-page Streamlit application
- Gemini API integration for text and image generation
- Local storage using Streamlit's session_state
- Structured output processing with Pydantic
- Light/dark theme support

## Setup and Usage

1. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

2. **Get a Gemini API key**:
   - Go to [Google AI Studio](https://ai.google.dev/) and create an API key
   - Create a `.env` file in the project root with: `GEMINI_API_KEY=your_api_key`

3. **Run the application**:
   ```
   streamlit run app.py
   ```

4. **Using the app**:
   - Enter your Gemini API key in the sidebar
   - Navigate between pages using the sidebar
   - Add ingredients and preferences in the Ingredients & Preferences page
   - Generate recipes using the Recipe Generator page
   - Save recipes to your collection
   - Customize settings as needed

## Requirements

- Python 3.8+
- Streamlit 1.28.0+
- Gemini API access (API key)
- Other dependencies as listed in requirements.txt

## Implementation Details

The application uses the Gemini 2.0 Flash experimental model for image generation alongside text generation. The app processes the streaming response from Gemini to extract text and images, structuring them into a cohesive recipe display with Pydantic models.

Recipe data is stored in Streamlit's session_state for persistence within a session. 
