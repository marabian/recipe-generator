# app.py
import os
import sys
import uuid
import time
from datetime import datetime

try:
    import streamlit as st
    from dotenv import load_dotenv
except ImportError:
    print("Required packages not found. Please install them using:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Import services and utilities
try:
    from services.gemini_service import generate_recipe, check_ingredient_availability
    from utils.display_functions import display_recipe
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure all project files are in the correct directories.")
    sys.exit(1)

# Load environment variables
load_dotenv()


def show_recipe_generator():
    """Show recipe generator page with input and generated recipes."""
    st.title("Recipe Generator")

    # Input area
    with st.form("recipe_generator_form"):
        prompt = st.text_area(
            "What would you like to cook?",
            placeholder="e.g., I want to make a quick dinner with pasta and vegetables",
            height=100,
        )

        # Create columns with better spacing for buttons
        left_col, right_col = st.columns([7.3, 1])

        with left_col:
            # Primary button for generating recipe
            generate_button = st.form_submit_button("🧑‍🍳 Generate Recipe", type="primary")

        with right_col:
            # Container for right-aligned clear button
            _, clear_col = st.columns([0.1, 0.9])
            with clear_col:
                clear_button = st.form_submit_button("🔄 Clear")

        # Option to check ingredients availability
        st.session_state.check_ingredients = st.checkbox(
            "Check ingredients against my pantry",
            value=st.session_state.check_ingredients,
            help="Compare recipe ingredients with your saved ingredients",
        )

    # Check for API key
    if not st.session_state.api_key:
        st.warning("Please enter your Gemini API key in the sidebar.")
        return

    # Clear input when clear button is clicked
    if clear_button:
        st.session_state.last_recipe = None
        st.rerun()

    # Store generated recipe or regenerate
    if generate_button:
        if not prompt and not st.session_state.ingredients:
            st.warning("Please enter a prompt or add ingredients in the Ingredients & Preferences page.")
            return

        with st.spinner("Generating recipe..."):
            # Generate the recipe
            recipe = generate_recipe(
                prompt=prompt,
                ingredients=st.session_state.ingredients,
                preferences=st.session_state.preferences,
                units=st.session_state.units,
                api_key=st.session_state.api_key,
            )

            if recipe:
                # Check ingredient availability once during generation
                availability_results = None
                if st.session_state.check_ingredients:
                    recipe_ingredients = recipe.model_dump()["ingredients"]
                    if not st.session_state.ingredients:
                        # If user has no ingredients, everything is unavailable
                        availability_results = {"available": [], "unavailable": recipe_ingredients}
                    else:
                        # Only call Gemini if user has ingredients to check against
                        availability_results = check_ingredient_availability(
                            recipe_ingredients, st.session_state.ingredients, st.session_state.api_key
                        )

                # Store the recipe in session state
                st.session_state.last_recipe = {
                    "id": str(uuid.uuid4()),
                    "prompt": prompt,
                    "recipe": recipe.model_dump(),
                    "generated_at": time.time(),
                    "availability_results": availability_results,
                }

                # Show success message
                st.success("Recipe generated successfully!")
            else:
                st.error("Failed to generate recipe. Please try again.")

    # Display the generated recipe
    if hasattr(st.session_state, "last_recipe") and st.session_state.last_recipe:
        display_recipe(st.session_state.last_recipe, check_availability=st.session_state.check_ingredients)

        # Save button
        if st.button("Save to Collection"):
            if "recipes" not in st.session_state:
                st.session_state.recipes = []

            # Check if recipe already exists in collection
            recipe_exists = False
            for recipe in st.session_state.recipes:
                if recipe["id"] == st.session_state.last_recipe["id"]:
                    recipe_exists = True
                    break

            if not recipe_exists:
                st.session_state.recipes.append(st.session_state.last_recipe)
                st.success("Recipe saved to collection!")
            else:
                st.info("This recipe is already in your collection.")


def show_recipe_collection():
    """Show all saved recipes in a collection."""
    st.title("Recipe Collection")

    # Check if there are any saved recipes
    if "recipes" not in st.session_state or not st.session_state.recipes:
        st.info("You haven't saved any recipes yet. Generate and save recipes to see them here.")
        return

    # Display number of recipes
    st.write(f"You have {len(st.session_state.recipes)} saved recipes.")

    # Add a button to clear all recipes
    if st.button("Clear All Recipes"):
        st.session_state.recipes = []
        st.success("All recipes cleared!")
        st.rerun()

    # Display all recipes
    for i, recipe_data in enumerate(st.session_state.recipes):
        with st.expander(f"{recipe_data['recipe']['title']}"):
            # Show when the recipe was generated
            if "generated_at" in recipe_data:
                generated_time = datetime.fromtimestamp(recipe_data["generated_at"])
                st.caption(f"Generated on {generated_time.strftime('%Y-%m-%d %H:%M:%S')}")

            # Show the original prompt
            st.write("**Original Prompt:**")
            st.write(recipe_data["prompt"])

            # Display the recipe
            display_recipe(recipe_data, check_availability=False)

            # Delete button
            if st.button("Delete Recipe", key=f"delete_{recipe_data['id']}"):
                st.session_state.recipes.remove(recipe_data)
                st.success("Recipe deleted!")
                st.rerun()


def show_ingredients_preferences():
    """Show page for managing ingredients and preferences."""
    st.title("Ingredients & Preferences")

    # Ingredients section
    st.header("Ingredients")
    st.write("Add ingredients from your pantry that you'd like to use in your recipes.")

    # Add ingredients form
    with st.form("add_ingredient_form"):
        col1, col2 = st.columns([3, 1])
        with col1:
            ingredient = st.text_input("Ingredient", placeholder="e.g., chicken, pasta, broccoli")
        with col2:
            add_button = st.form_submit_button("Add")

    if add_button and ingredient:
        if "ingredients" not in st.session_state:
            st.session_state.ingredients = []

        # Add only if not already in the list
        if ingredient not in st.session_state.ingredients:
            st.session_state.ingredients.append(ingredient)
            st.success(f"Added {ingredient} to your ingredients list!")
        else:
            st.info(f"{ingredient} is already in your ingredients list.")

    # Display ingredients
    if "ingredients" in st.session_state and st.session_state.ingredients:
        st.subheader("Your Ingredients")

        # Display ingredients as a list with remove buttons
        for i, ing in enumerate(st.session_state.ingredients):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(ing)
            with col2:
                if st.button("Remove", key=f"remove_{i}"):
                    st.session_state.ingredients.remove(ing)
                    st.success(f"Removed {ing} from your ingredients list!")
                    st.rerun()

        # Button to clear all ingredients
        if st.button("Clear All Ingredients"):
            st.session_state.ingredients = []
            st.success("All ingredients cleared!")
            st.rerun()
    else:
        st.info("Your ingredients list is empty. Add ingredients from pantry above.")

    # Preferences section
    st.markdown("---")
    st.header("Preferences")
    st.write("Add your culinary preferences, dietary restrictions, or other special requests.")

    # Preferences input
    preferences = st.text_area(
        "Preferences",
        value=st.session_state.preferences if "preferences" in st.session_state else "",
        placeholder="e.g., vegetarian, low-carb, spicy, gluten-free, quick meals under 30 minutes",
    )

    # Save preferences button
    if st.button("Save Preferences"):
        st.session_state.preferences = preferences
        st.success("Preferences saved!")

    # Inform user about current preferences
    if "preferences" in st.session_state and st.session_state.preferences:
        st.info(f"Current preferences: {st.session_state.preferences}")
    else:
        st.info("No preferences set. Add your preferences above.")


def show_settings():
    """Show settings page for units and theme preferences."""
    st.title("Settings")

    # Units selection
    st.header("Measurement Units")
    st.write("Choose your preferred measurement units for recipes.")

    units = st.radio(
        "Units",
        options=["metric", "imperial"],
        index=0 if st.session_state.units == "metric" else 1,
        help="Metric uses grams, milliliters, etc. Imperial uses ounces, cups, etc.",
        horizontal=True,
    )

    if units != st.session_state.units:
        st.session_state.units = units
        st.success(f"Units set to {units}!")

    # Gemini API key
    st.markdown("---")
    st.header("API Key")
    st.write("Your Gemini API key is used to generate recipes.")

    # Obscure the API key for display
    if st.session_state.api_key:
        masked_key = (
            st.session_state.api_key[:4] + "*" * (len(st.session_state.api_key) - 8) + st.session_state.api_key[-4:]
        )
        st.info(f"Current API key: {masked_key}")
        st.write("You can update your API key in the sidebar.")
    else:
        st.warning("No API key set. Please enter your Gemini API key in the sidebar.")


def main():
    # Set page config
    st.set_page_config(
        page_title="Recipe Generator",
        page_icon="🍳",
        layout="wide",
    )

    # Initialize session state variables if they don't exist
    if "recipes" not in st.session_state:
        st.session_state.recipes = []

    if "ingredients" not in st.session_state:
        st.session_state.ingredients = []

    if "preferences" not in st.session_state:
        st.session_state.preferences = ""

    if "units" not in st.session_state:
        st.session_state.units = "metric"

    if "api_key" not in st.session_state:
        st.session_state.api_key = os.getenv("GEMINI_API_KEY", "")

    if "check_ingredients" not in st.session_state:
        st.session_state.check_ingredients = False

    # Sidebar for navigation and API key
    with st.sidebar:
        st.title("Recipe Generator")

        # Navigation
        page = st.radio(
            "Navigate to",
            ["Recipe Generator", "Recipe Collection", "Ingredients & Preferences", "Settings"],
            label_visibility="collapsed",
        )

        # API Key input
        st.markdown("---")
        api_key = st.text_input("Gemini API Key", value=st.session_state.api_key, type="password")

        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
            st.success("API Key updated!")

    # Display selected page
    if page == "Recipe Generator":
        show_recipe_generator()
    elif page == "Recipe Collection":
        show_recipe_collection()
    elif page == "Ingredients & Preferences":
        show_ingredients_preferences()
    elif page == "Settings":
        show_settings()


if __name__ == "__main__":
    main()
