# Streamlit Recipe Generator

## Overview

This is a Streamlit web application that allows users to generate recipes based on a set of ingredients. It will provide step by step instructions on how to cook the recipe using Gemini's native text and image generation capabilities.


# High-level architecture

Streamlit app with the following tabs:

- Recipe Generator
- Recipe Collection
- Ingredients & Preferences
- Settings

Sidebar will have buttons for each of the pages. On the bottom of the sidebar, there will be an input to enter your own Gemini API key.

## Recipe Generator Page

- Text input area for the user to enter a text prompt to generate a recipe. 
- Button to submit the prompt and generate a recipe.
- Clear button to clear the input and start fresh.
- Regenerate button to regenerate the recipe.
- Button to save the recipe to the recipe collection (local storage)
- Recipe output will be a step by step text instructions and images.

## Recipe Collection Page

- Display all the recipes saved in the local storage.
- Each recipe card will have a button to delete the recipe from the local storage.
- Each recipe card will have a button to view the recipe details (input prompt and output recipe)

## Ingredients & Preferences Page

- Top area of the page will be for ingredients.
- Text input area for the user to enter a single ingredient.
- Button to add the ingredient to the list of ingredients.
- List of added ngredients will be displayed in a card.
- Button next to each ingredient to remove it from the list.
- Button to clear the list of ingredients.

- Bottom area of the page will be for preferences. This will be a simple text input area for the user to enter their preferences in free form text which we'll inject into the recipe generation prompt.

## Settings Page

- User can pick imperial or metric units (this will be injected into the recipe generation prompt)

## Low-level architecture

- Streamlit app should live in app.py
- Use Streamlit components for the UI
- Use Gemini API for the recipe generation
- Use local storage to save the recipes
- A services file/layer for all the functions that call the Gemini API
- Prompts folder for all the system prompts used in the app
- Uses new Gemini Developer API/Python SDK
- Use structured outputs from Gemini API with Pydantic to get the recipe in a structured format
- Make sure of Gemini's ability to output text and inline images (interleaving text and images in the output)

## Documentation

- Create a README.md file for the project explaining the purpose of the project, the architecture and structure of the project, and how to run the project.

## Gemini API Example (From AI Studio)

```python
import base64
import os
import mimetypes
from google import genai
from google.genai import types


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()


def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.0-flash-exp-image-generation"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""generate me a recipe i can cook in the air fryer with chicken.

I want images for each step along with description on what to do

Make sure to have a human in the images performing the actions"""),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""## Crispy & Juicy Air Fryer Chicken Thighs with Garlic Herb Marinade

This recipe yields incredibly flavorful and crispy chicken thighs with minimal effort, all thanks to the magic of the air fryer.

**Yields:** 2 servings
**Prep time:** 15 minutes (plus at least 30 minutes marinating)
**Cook time:** 18-20 minutes

**Ingredients:**

*   2 boneless, skinless chicken thighs (about 6-8 oz each)
*   1 tablespoon olive oil
*   1 tablespoon lemon juice
*   1 teaspoon dried Italian herbs
*   1/2 teaspoon garlic powder
*   1/4 teaspoon salt
*   1/4 teaspoon black pepper
*   Optional: Fresh parsley, chopped, for garnish

---

**Step 1: Prepare the Marinade**

"""),
                types.Part.from_bytes(
                    mime_type="""image/png""",
                    data=base64.b64decode(
                    ),
                ),
                types.Part.from_text(text="""In a small bowl, combine the olive oil, lemon juice, dried Italian herbs, garlic powder, salt, and black pepper. Stir well with a spoon until the marinade is evenly mixed.

---

**Step 2: Marinate the Chicken**

"""),
                types.Part.from_bytes(
                    mime_type="""image/png""",
                    data=base64.b64decode(
                    ),
                ),
                types.Part.from_text(text="""Place the chicken thighs in the bowl with the marinade. Use your hands to rub the marinade all over the chicken, ensuring each piece is well coated. Cover the bowl with plastic wrap or transfer the chicken to a resealable plastic bag. Marinate in the refrigerator for at least 30 minutes, or up to 4 hours for more intense flavor.

---

**Step 3: Preheat the Air Fryer (Optional but Recommended)**

"""),
                types.Part.from_bytes(
                    mime_type="""image/png""",
                    data=base64.b64decode(
                    ),
                ),
                types.Part.from_text(text="""Preheat your air fryer to 400°F (200°C) for 3-5 minutes. This step can help the chicken cook more evenly and achieve a crispier exterior.

---

**Step 4: Place Chicken in the Air Fryer Basket**

"""),
                types.Part.from_bytes(
                    mime_type="""image/png""",
                    data=base64.b64decode(
                    ),
                ),
                types.Part.from_text(text="""Remove the chicken thighs from the marinade and place them in the air fryer basket in a single layer. Avoid overcrowding the basket; cook in batches if necessary to ensure even cooking and crisping.

---

**Step 5: Air Fry the Chicken**

"""),
                types.Part.from_bytes(
                    mime_type="""image/png""",
                    data=base64.b64decode(
                    ),
                ),
                types.Part.from_text(text="""Air fry for 10 minutes. Then, using tongs, carefully flip the chicken thighs. Continue air frying for another 8-10 minutes, or until the internal temperature of the chicken reaches 165°F (74°C) using a meat thermometer inserted into the thickest part of the thigh. The exact cooking time may vary slightly depending on the thickness of the chicken and your air fryer model.

---

**Step 6: Rest and Serve**

"""),
                types.Part.from_bytes(
                    mime_type="""image/png""",
                    data=base64.b64decode(
                    ),
                ),
                types.Part.from_text(text="""Once cooked through, carefully remove the chicken thighs from the air fryer and place them on a clean plate. Let the chicken rest for 2-3 minutes before serving. This allows the juices to redistribute, resulting in more tender and flavorful chicken. Garnish with fresh parsley, if desired.

Enjoy your crispy and juicy air fryer chicken thighs! They are delicious served with your favorite sides like roasted vegetables, rice, or a fresh salad."""),
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""INSERT_INPUT_HERE"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_modalities=[
            "image",
            "text",
        ],
        safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_CIVIC_INTEGRITY",
                threshold="OFF",  # Off
            ),
        ],
        response_mime_type="text/plain",
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
            continue
        if chunk.candidates[0].content.parts[0].inline_data:
            file_name = "ENTER_FILE_NAME"
            inline_data = chunk.candidates[0].content.parts[0].inline_data
            file_extension = mimetypes.guess_extension(inline_data.mime_type)
            save_binary_file(
                f"{file_name}{file_extension}", inline_data.data
            )
            print(
                "File of mime type"
                f" {inline_data.mime_type} saved"
                f"to: {file_name}"
            )
        else:
            print(chunk.text)

if __name__ == "__main__":
    generate()
```
