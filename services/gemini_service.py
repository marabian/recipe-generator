# services/gemini_service.py
import base64
import mimetypes
import tempfile
from typing import List, Optional, Dict
from pydantic import BaseModel
from google import genai
from google.genai import types

from prompts.recipe_prompts import RECIPE_SYSTEM_PROMPT


class RecipeStep(BaseModel):
    """A single step in a recipe with description and optional image."""

    description: str
    image_data: Optional[str] = None
    image_mime_type: Optional[str] = None


class Recipe(BaseModel):
    """A structured recipe with title, ingredients, and steps."""

    title: str
    description: str
    ingredients: List[str]
    prep_time: str
    cook_time: str
    servings: int
    steps: List[RecipeStep]


def initialize_gemini(api_key: str):
    """Initialize the Gemini client with the provided API key."""
    if not api_key:
        raise ValueError("API key is required")

    return genai.Client(api_key=api_key)


def check_ingredient_availability(
    recipe_ingredients: List[str], user_ingredients: List[str], api_key: str
) -> Dict[str, List[str]]:
    """Check which recipe ingredients the user has in their pantry using Gemini function calling.

    Args:
        recipe_ingredients: List of ingredients from the recipe
        user_ingredients: List of ingredients saved by the user
        api_key: Gemini API key

    Returns:
        Dictionary with 'available' and 'unavailable' lists of ingredients
    """
    try:
        print(f"DEBUG - Checking ingredient availability with Gemini API key: {api_key}")
        client = initialize_gemini(api_key)

        # Define the function that Gemini will call
        def categorize_ingredients(ingredients: List[str]) -> Dict[str, List[str]]:
            """Categorizes recipe ingredients into available and unavailable based on user's pantry.

            Args:
                ingredients: List of recipe ingredients to categorize

            Returns:
                Dictionary with 'available' and 'unavailable' lists
            """
            available = []
            unavailable = []

            for ingredient in ingredients:
                # Check if any user ingredient is part of this recipe ingredient
                found = False
                for user_ingredient in user_ingredients:
                    # Simple string matching - can be improved for more complex matching
                    if user_ingredient.lower() in ingredient.lower():
                        available.append(ingredient)
                        found = True
                        break

                if not found:
                    unavailable.append(ingredient)

            return {"available": available, "unavailable": unavailable}

        # Use a simpler model for function calling
        model = "gemini-2.0-flash-lite"

        # Prepare the prompt
        prompt = f"""
        I have a recipe with these ingredients: {', '.join(recipe_ingredients)}
        
        I have these ingredients available in my pantry: {', '.join(user_ingredients)}
        
        Please categorize the recipe ingredients into 'available' and 'unavailable' based on what I have in my pantry.
        """

        # Configure function calling
        generate_content_config = types.GenerateContentConfig(
            tools=[categorize_ingredients],
        )

        # Generate the response with function calling
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=generate_content_config,
        )

        # Check if there's a function call in the response
        if (
            response.candidates
            and response.candidates[0].content
            and response.candidates[0].content.parts
            and hasattr(response.candidates[0].content.parts[0], "function_call")
        ):

            # Get the function call result
            function_call = response.candidates[0].content.parts[0].function_call

            # If the function is our categorize_ingredients function
            if function_call and function_call.name == "categorize_ingredients":
                # Extract and return the categorized ingredients
                return categorize_ingredients(function_call.args.get("ingredients", recipe_ingredients))

        # If no function call or something went wrong, categorize manually
        return categorize_ingredients(recipe_ingredients)

    except Exception as e:
        print(f"DEBUG - Error checking ingredient availability: {e}")
        # Fallback - attempt simple matching
        return categorize_ingredients(recipe_ingredients)


def generate_recipe(
    prompt: str, ingredients: List[str], preferences: str, units: str, api_key: str
) -> Optional[Recipe]:
    """Generate a recipe using Gemini API based on user input and preferences."""
    try:
        client = initialize_gemini(api_key)

        # Build the complete prompt
        # Note: Developer/system instruction is not enabled for models/gemini-2.0-flash-exp-image-generation
        complete_prompt = f"{RECIPE_SYSTEM_PROMPT}\n\n{prompt}\n\n"

        if ingredients:
            complete_prompt += f"Ingredients to use: {', '.join(ingredients)}\n"

        if preferences:
            complete_prompt += f"Preferences: {preferences}\n"

        complete_prompt += f"Please use {units} units for measurements.\n"
        complete_prompt += "Generate a detailed recipe with step-by-step instructions and images for each step."

        # Print the full prompt for debugging
        print("DEBUG - Complete prompt:")
        print(complete_prompt)

        # Use the Gemini 2.0 Flash experimental model for image generation
        model = "gemini-2.0-flash-exp-image-generation"
        print(f"DEBUG - Using model: {model}")

        # Create the request with only user role (no system role)
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=complete_prompt),
                ],
            ),
        ]

        # Configure the response to include both text and images
        generate_content_config = types.GenerateContentConfig(
            # Explicitly specify we want both text and image in the response
            response_modalities=["Text", "Image"],
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="BLOCK_MEDIUM_AND_ABOVE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="BLOCK_MEDIUM_AND_ABOVE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="BLOCK_MEDIUM_AND_ABOVE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_MEDIUM_AND_ABOVE",
                ),
            ],
        )

        # Process the streaming response to build the recipe
        title = ""
        description = ""
        ingredients_list = []
        steps = []
        prep_time = ""
        cook_time = ""
        servings = 0

        current_step = None
        current_step_num = 0
        pending_images = []  # Store images that come in before their step
        accumulated_text = ""  # Accumulate text for later parsing
        print("DEBUG - Starting to stream content from Gemini")

        received_chunks = 0
        image_chunks = 0
        text_chunks = 0

        # Stream the response
        try:
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                received_chunks += 1

                # Process the chunk to extract content
                if not chunk.candidates or not chunk.candidates[0].content:
                    print("DEBUG - Received chunk with no content")
                    continue

                # Process parts in the chunk
                if not chunk.candidates[0].content.parts:
                    print("DEBUG - Received chunk with empty parts array")
                    continue

                # Iterate through parts in the chunk
                for part in chunk.candidates[0].content.parts:
                    # Handle text part
                    if hasattr(part, "text") and part.text:
                        text_chunks += 1
                        text = part.text
                        print(f"DEBUG - Received text chunk ({len(text)} chars): {text[:100]}...")

                        # Accumulate text for later processing
                        accumulated_text += text

                        # Extract title if not already set
                        if not title and "##" in text:
                            split_text = text.split("##")
                            if len(split_text) > 1:
                                title_sections = split_text[1].strip().split("\n")
                                if title_sections:
                                    title = title_sections[0]
                                    print(f"DEBUG - Extracted title: {title}")

                        # Extract description
                        if "**Prep time:**" in text:
                            description_parts = text.split("**Prep time:**")[0].strip()
                            if "**" in description_parts:
                                description_split = description_parts.split("**")
                                if len(description_split) > 1:
                                    description = description_split[-1].strip()
                                    print(f"DEBUG - Extracted description: {description[:50]}...")

                        # Extract prep time
                        if "**Prep time:**" in text:
                            prep_parts = text.split("**Prep time:**")[1].split("\n")[0].strip()
                            if prep_parts:
                                prep_time = prep_parts
                                print(f"DEBUG - Extracted prep time: {prep_time}")

                        # Extract cook time
                        if "**Cook time:**" in text:
                            cook_parts = text.split("**Cook time:**")[1].split("\n")[0].strip()
                            if cook_parts:
                                cook_time = cook_parts
                                print(f"DEBUG - Extracted cook time: {cook_time}")

                        # Extract servings
                        if "**Servings:**" in text:
                            try:
                                servings_text = text.split("**Servings:**")[1].split("\n")[0].strip()
                                servings = int(servings_text.split()[0])
                                print(f"DEBUG - Extracted servings: {servings}")
                            except Exception:
                                servings = 2  # Default if parsing fails
                                print(f"DEBUG - Failed to parse servings, using default: {servings}")

                        # Detect step markers in the text
                        if "**Step " in text:
                            # Extract all steps in this text chunk
                            step_parts = text.split("**Step ")

                            # Start from 1 to skip the content before the first step
                            for i in range(1, len(step_parts)):
                                step_text = step_parts[i]
                                step_num = 0

                                # Try to extract the step number
                                try:
                                    step_num_text = step_text.split(":", 1)[0].strip()
                                    step_num = int(step_num_text)
                                except (ValueError, IndexError):
                                    step_num = current_step_num + 1

                                # Extract step description
                                if ":**" in step_text:
                                    # Extract step description
                                    step_desc = step_text.split(":**", 1)[1]

                                    # Clean up description
                                    if "---" in step_desc:
                                        step_desc = step_desc.split("---")[0].strip()
                                    elif "**Step " in step_desc and i < len(step_parts) - 1:
                                        # If there's another step after this
                                        step_desc = step_desc.split("**Step ")[0].strip()
                                    else:
                                        step_desc = step_desc.strip()

                                    # Create the step and add it to our list
                                    new_step = RecipeStep(description=step_desc)

                                    # Set as current step for upcoming images
                                    current_step = new_step
                                    current_step_num = step_num
                                    steps.append(new_step)

                                    print(f"DEBUG - Created step {step_num} with description: {step_desc[:50]}...")

                                    # Check if we have any pending images to attach to this step
                                    if pending_images and len(steps) == 1:
                                        # Only attach the first pending image to this first step
                                        img_data, mime = pending_images[0]
                                        new_step.image_data = img_data
                                        new_step.image_mime_type = mime
                                        print(f"DEBUG - Attached pending image to step {step_num}")
                                        pending_images.pop(0)  # Remove the used image

                    # Handle image part
                    elif hasattr(part, "inline_data") and part.inline_data:
                        image_chunks += 1
                        mime_type = part.inline_data.mime_type
                        image_data = base64.b64encode(part.inline_data.data).decode("utf-8")

                        print(f"DEBUG - Received image data with mime type: {mime_type}")

                        # If we have a current step, attach the image to it
                        if current_step:
                            # Only attach if the step doesn't already have an image
                            if not current_step.image_data:
                                current_step.image_data = image_data
                                current_step.image_mime_type = mime_type
                                print(f"DEBUG - Attached image to step {current_step_num}")
                            else:
                                # Store for the next step
                                pending_images.append((image_data, mime_type))
                                print("DEBUG - Current step already has an image, storing for later")
                        else:
                            # Store the image for when we have a step to attach it to
                            pending_images.append((image_data, mime_type))
                            print("DEBUG - Storing image for later attachment")

            print(
                f"DEBUG - Finished streaming. Received {received_chunks} chunks total: {text_chunks} text, {image_chunks} images"
            )

            # If we don't have any steps yet, extract them from accumulated text
            if not steps and accumulated_text:
                print("DEBUG - No steps extracted during streaming, extracting from accumulated text")

                # Extract steps using regex pattern matching
                import re

                step_pattern = r"\*\*Step (\d+):\s*([^*]+)\*\*\s*(.*?)(?=\*\*Step \d+:|$)"
                matches = re.findall(step_pattern, accumulated_text, re.DOTALL)

                for match in matches:
                    step_num = int(match[0]) if match[0].isdigit() else 0
                    step_title = match[1].strip()
                    step_desc = match[2].strip()

                    if "---" in step_desc:
                        step_desc = step_desc.split("---")[0].strip()

                    # Create step with complete information
                    full_desc = f"{step_title}: {step_desc}"
                    step = RecipeStep(description=full_desc)
                    steps.append(step)
                    print(f"DEBUG - Extracted step {step_num} from regex: {full_desc[:50]}...")

                # If regex failed, try another approach
                if not steps:
                    print("DEBUG - Regex extraction failed, trying simpler approach")
                    step_sections = accumulated_text.split("**Step ")

                    for i in range(1, len(step_sections)):
                        step_text = step_sections[i]

                        # Extract step number and description
                        if ":**" in step_text:
                            step_desc = step_text.split(":**")[1]

                            if "---" in step_desc:
                                step_desc = step_desc.split("---")[0].strip()
                            elif "**Step " in step_desc:
                                step_desc = step_desc.split("**Step ")[0].strip()
                            else:
                                step_desc = step_desc.strip()

                            # Create the step
                            step = RecipeStep(description=step_desc)
                            steps.append(step)
                            print(f"DEBUG - Extracted step {i} with simple approach: {step_desc[:50]}...")

            # Attach any pending images to steps that don't have images
            if pending_images and steps:
                print(f"DEBUG - Attaching {len(pending_images)} pending images to steps without images")

                for step in steps:
                    if not step.image_data and pending_images:
                        img_data, mime = pending_images.pop(0)
                        step.image_data = img_data
                        step.image_mime_type = mime
                        print("DEBUG - Attached pending image to step")

                        if not pending_images:
                            break

            # Extract ingredients from accumulated text if we don't have any
            if not ingredients_list:
                print("DEBUG - Extracting ingredients from accumulated text")

                if "**Ingredients:**" in accumulated_text:
                    ingredients_section = accumulated_text.split("**Ingredients:**")[1]

                    # Determine where the ingredients section ends
                    if "**Step 1" in ingredients_section:
                        ingredients_section = ingredients_section.split("**Step 1")[0]
                    elif "---" in ingredients_section:
                        ingredients_section = ingredients_section.split("---")[0]

                    # Process ingredients
                    ingredients_list = []
                    for line in ingredients_section.split("\n"):
                        line = line.strip()
                        if line and (line.startswith("*") or line.startswith("-")):
                            ingredient = line.lstrip("*- ").strip()
                            if ingredient:
                                ingredients_list.append(ingredient)

                    print(f"DEBUG - Extracted {len(ingredients_list)} ingredients from accumulated text")

            # Extract title from accumulated text if we don't have one
            if not title and accumulated_text:
                print("DEBUG - Extracting title from accumulated text")
                if "##" in accumulated_text:
                    title_candidate = accumulated_text.split("##")[1].strip().split("\n")[0]
                    if title_candidate:
                        title = title_candidate

        except Exception as stream_error:
            print(f"DEBUG - Error while streaming content: {stream_error}")
            # Continue with what we have so far, rather than failing completely

        print(
            f"DEBUG - Final recipe data - Title: '{title}', Description: '{description[:20] if description else ''}...', "
            f"Ingredients: {len(ingredients_list)}, Steps: {len(steps)}"
        )

        # Create the recipe object
        recipe = Recipe(
            title=title if title else "Delicious Recipe",
            description=description if description else "A tasty recipe made with your ingredients",
            ingredients=ingredients_list,
            prep_time=prep_time if prep_time else "15 minutes",
            cook_time=cook_time if cook_time else "30 minutes",
            servings=servings if servings else 2,
            steps=steps,
        )

        return recipe

    except Exception as e:
        print(f"DEBUG - Fatal error generating recipe: {e}")
        return None


def save_image_to_temp(base64_data: str, mime_type: str) -> str:
    """Save base64 encoded image data to a temporary file and return the file path."""
    if not base64_data:
        return ""

    try:
        # Decode the base64 data
        binary_data = base64.b64decode(base64_data)

        # Determine the file extension
        extension = mimetypes.guess_extension(mime_type)
        if not extension:
            extension = ".png"  # Default to png

        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
        temp_file.write(binary_data)
        temp_file.close()

        return temp_file.name
    except Exception as e:
        print(f"DEBUG - Error saving image: {e}")
        return ""
