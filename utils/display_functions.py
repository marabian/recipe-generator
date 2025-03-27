# utils/display_functions.py
import streamlit as st
import os
from PIL import Image
from services.gemini_service import save_image_to_temp


def display_recipe(recipe_data, check_availability=False):
    """Display a recipe with title, ingredients, and steps with images.

    Args:
        recipe_data: Dictionary containing recipe information
        check_availability: Whether to check ingredient availability against user's pantry
    """
    recipe = recipe_data["recipe"]

    # Display recipe title and info
    st.markdown(f"## {recipe['title']}")
    st.markdown(f"*{recipe['description']}*")

    # Display recipe metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Prep time:** {recipe['prep_time']}")
    with col2:
        st.markdown(f"**Cook time:** {recipe['cook_time']}")
    with col3:
        st.markdown(f"**Servings:** {recipe['servings']}")

    # Display ingredients
    st.markdown("### Ingredients")

    # Check if we should display categorized ingredients
    if check_availability and recipe_data.get("availability_results"):
        availability_results = recipe_data["availability_results"]

        # Show available ingredients in green
        if availability_results.get("available"):
            st.markdown("#### Available in your pantry:")
            for ingredient in availability_results["available"]:
                st.markdown(f"- <span style='color:green'>{ingredient}</span>", unsafe_allow_html=True)

        # Show unavailable ingredients in red
        if availability_results.get("unavailable"):
            st.markdown("#### Need to buy:")
            for ingredient in availability_results["unavailable"]:
                st.markdown(f"- <span style='color:red'>{ingredient}</span>", unsafe_allow_html=True)
    else:
        # Display ingredients normally if not checking availability
        for ingredient in recipe["ingredients"]:
            st.markdown(f"- {ingredient}")

    # Display steps with images
    st.markdown("### Instructions")

    # Check if we have steps to display
    if not recipe["steps"]:
        st.info("No detailed instructions were generated for this recipe. You may need to regenerate it.")
        return

    # Display each step with its image
    for i, step in enumerate(recipe["steps"]):
        with st.container():
            st.markdown(f"**Step {i+1}:** {step['description']}")

            # If there's an image, display it
            if step.get("image_data") and step.get("image_mime_type"):
                try:
                    # Save the image to a temporary file
                    image_path = save_image_to_temp(step["image_data"], step["image_mime_type"])

                    if image_path and os.path.exists(image_path):
                        # Display the image
                        image = Image.open(image_path)
                        st.image(image, use_container_width=True)

                        # Clean up temporary file
                        try:
                            os.remove(image_path)
                        except Exception as e:
                            print(f"Error removing temporary file: {e}")
                except Exception as e:
                    st.error(f"Failed to load image: {e}")

            st.markdown("---")
