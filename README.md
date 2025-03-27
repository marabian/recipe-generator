# Streamlit Recipe Generator

A Streamlit web application that allows users to generate recipes based on ingredients using Gemini's text and image generation capabilities.

## Features

### Implemented Features
- [x] **Recipe Generation**: Generate detailed recipes with step-by-step instructions and images
- [x] **Structured Output**: Uses Pydantic for structured recipe data modeling and validation
- [x] **Interleaved Content**: Seamless integration of text instructions with corresponding images
- [x] **Recipe Collection**: Save and manage your favorite recipes
- [x] **Ingredients Management**: Add, remove, and clear ingredients to be used in recipes
- [x] **Preference Settings**: Set culinary preferences and dietary restrictions
- [x] **Customizable Units**: Toggle between metric and imperial measurement units
- [x] **Streamlined UI**: Intuitive interface with responsive design and primary/secondary button hierarchy

### Planned Features
- [ ] **Pantry Awareness**: Highlight ingredients you already have in your pantry (green) versus those you need (red)
- [ ] **Nutritional Analysis**: Calculate and display nutritional information for each recipe with visual charts
- [ ] **Consumption Tracking**: Optional feature to track nutritional intake based on recipes you've made
- [ ] **Dark/Light Theme**: Customizable appearance settings

### Things to Fix

- [ ] Use structured outputs with Pydantic native with Gemini
- [ ] Make sure the old recipe refreshes when new recipe is being generated

## Architecture

### Project Structure

```
recipe-generator/
├── app.py                  # Main application
├── requirements.txt        # Project dependencies
├── README.md               # Documentation
├── services/               # Service layer
│   └── gemini_service.py   # Gemini API integration
├── utils/                  # Utility functions
│   └── display_functions.py # Display and rendering utilities
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
