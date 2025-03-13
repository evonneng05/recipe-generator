import streamlit as st
import google.generativeai as genai
from PIL import Image
import pdfkit
import json
import os
import torch
from image_generator import generate_recipe_image
from dotenv import load_dotenv
torch.classes.__path__ = []
load_dotenv()

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def generate_recipes(ingredients, dietary, food_type):
    print("Generating recipes...")
    prompt = f"""
    Generate 3 unique recipes using these ingredients: {ingredients}. If needed, you can add other ingredients. For each ingredient, can you estimate the typical price range in Singapore dollars?
    For each ingredient, add in the weight required as well.
    Dietary Restrictions: {dietary}.
    Preferred Food Type: {food_type}.
    In the steps, add in numbers before the step. (e.g. 1. Wash the rice)

    Return the response in **strict JSON format**:
    {{
        "recipes": [
            {{
                "title": "Recipe Title 1",
                "ingredients": [
                    {{"name": "ingredient1", "weight": "100g", "cost": "$10.00"}},
                    {{"name": "ingredient2", "weight": "200ml", "cost": "$10.00"}}
                ],
                "steps": ["Step 1", "Step 2"]
            }},
            {{
                "title": "Recipe Title 2",
                "ingredients": [
                    {{"name": "ingredient1", "weight": "50g", "cost": "$15.00"}},
                    {{"name": "ingredient2", "weight": "150ml", "cost": "$2.00"}}
                ],
                "steps": ["Step 1", "Step 2"]
            }},
            {{
                "title": "Recipe Title 2",
                "ingredients": [
                    {{"name": "ingredient1", "weight": "50g", "cost": "$15.00"}},
                    {{"name": "ingredient2", "weight": "150ml", "cost": "$2.00"}}
                ],
                "steps": ["Step 1", "Step 2"]
            }}
        ]
    }}
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt).candidates[0].content.parts[0].text
    print("Recipes generated successfully!")

    cleaned_response = response.strip().strip("```json").strip("```")
    print(cleaned_response)

    try:
        recipes = json.loads(cleaned_response)["recipes"]
        return recipes
    except (KeyError, json.JSONDecodeError) as e:
        print("Error parsing recipes JSON:", e)
        return []

def get_nutrition_info(recipe):
    print("Generating nutrition info...")
    prompt = f"""
    Based on the following details, estimate the nutrition facts:
    
    Recipe Title: {recipe['title']}
    Ingredients: {''.join(f'<li>{ing["name"]} - {ing["weight"]}</li>' for ing in recipe['ingredients'])}
    
    Return the response in strict **JSON format**:
    {{
        "calories": "XXX kcal",
        "protein": "X g",
        "carbohydrates": "X g",
        "fat": "X g"
    }}
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt).candidates[0].content.parts[0].text
    cleaned_response = response.strip().strip("```json").strip("```")
    print("Nutrition info generated successfully!")

    try:
        nutrition_data = json.loads(cleaned_response)
        return nutrition_data
    except (KeyError, json.JSONDecodeError):
        print("Error parsing nutrition JSON")
        return {}

def add_links(ing):
    ing["ntuc"] = f'https://www.fairprice.com.sg/search?query={ing["name"]}'.replace(" ", "%20")
    ing["shengsiong"] = f'https://shengsiong.com.sg/search/{ing["name"]}'.replace(" ", "%20")
    ing['coldstorage'] = f'https://coldstorage.com.sg/en/search?keyword={ing["name"]}&page=1'.replace(" ", "%20")

def extract_missing_ingredients(recipe_ingredients, user_ingredients):
    print("Extracting missing ingredients...")
    user_ingredients_list = [ing.strip().lower() for ing in user_ingredients.split(",")]
    missing_ingredients = []
    for recipe_ing in recipe_ingredients:
        recipe_ing_name = recipe_ing["name"].lower()
        if not any(user_ing in recipe_ing_name for user_ing in user_ingredients_list if user_ing):
            missing_ingredients.append({
                "name": recipe_ing["name"],
                "cost": recipe_ing["cost"]
            })
    
    return missing_ingredients

def get_food_emoji(title):
    """Returns an appropriate emoji based on the recipe title/type"""
    title_lower = title.lower()
    if 'soup' in title_lower:
        return '🥣'
    elif 'noodle' in title_lower:
        return '🍜'
    elif 'rice' in title_lower:
        return '🍚'
    elif 'salad' in title_lower:
        return '🥗'
    elif 'dessert' in title_lower or 'cake' in title_lower:
        return '🍰'
    elif 'bread' in title_lower:
        return '🍞'
    elif 'pizza' in title_lower:
        return '🍕'
    elif 'chicken' in title_lower:
        return '🍗'
    elif 'meat' in title_lower:
        return '🥩'
    else:
        return '🍽️'


def format_recipe_html(recipe, for_pdf=False):
    """Formats a recipe's details into an HTML string for display."""
    emoji = "" if for_pdf else get_food_emoji(recipe['title'])
    
    html_content = f"""
    <div class='recipe'>
        <h2>{recipe['title']} {emoji}</h2>
        {'<img src="' + recipe["image_path"] + '" />' if recipe.get("image_path") else ''}
        <div class='nutrition-info'>
            <p style='font-weight: bold;'>Nutrition Information:</p>
            <p>Calories: {recipe['nutrition']['calories']}</p>
            <p>Protein: {recipe['nutrition']['protein']}</p>
            <p>Carbohydrates: {recipe['nutrition']['carbohydrates']}</p>
            <p>Fat: {recipe['nutrition']['fat']}</p>
        </div>
        
        <h3>Ingredients</h3>
        <ul>
            {''.join(f'<li>{ing["name"]} - {ing["weight"]}</li>' for ing in recipe['ingredients'])}
        </ul>
        
        <h3>Ingredients to purchase</h3>
        <ul>
    """

    for ingredient in recipe["missing_ingredients"]:
        html_content += f'''<li>{ingredient["name"].capitalize()} - {ingredient["cost"]} Buy here: (<a href='{ingredient["ntuc"]}'>NTUC</a>) (<a href='{ingredient["shengsiong"]}'>Sheng Siong</a>) (<a href='{ingredient["coldstorage"]}'>Cold Storage</a>)</li>'''

    html_content += """
        </ul>
        <h3>Steps</h3>
        <ul>
            {}
        </ul>
    """.format(''.join(f'<li>{step}</li>' for step in recipe['steps']))

    html_content += "</div>"
    return html_content


def create_pdf(recipe):
    """Generates a PDF from recipes using formatted HTML."""
    file_name = recipe["image_path"].replace(".png", ".pdf").replace("_image", "")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, recipe["image_path"])
    
    html_content = """
    <html>
    <head><style>
    body { font-family: 'Source Sans Pro', sans-serif; }
    h2 { color: #333; margin: 20px 0; }
    .recipe { margin-bottom: 20px; padding: 10px; border-radius: 10px; }
    ul, ol { margin-left: 20px; }
    li { line-height: 1.8; margin: 10px 0; }
    p { line-height: 1.6; margin: 10px 0; }
    a { color: #333; }
    img { 
        max-width: 50%; 
        border-radius: 10px; 
        margin: 20px auto;
        display: block;
    }
    </style></head>
    <body>
    """

    recipe_html = format_recipe_html(recipe, for_pdf=True)
    if os.path.exists(image_path):
        recipe_html = recipe_html.replace(
            recipe["image_path"],
            f'file://{image_path}'
        )
    
    html_content += recipe_html
    html_content += "</body></html>"

    try:
        options = {
            'enable-local-file-access': None
        }
        pdfkit.from_string(html_content, file_name, options=options)
        return file_name
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None

st.title("🍓 Recipe Generator 🍰")

st.subheader("Input ingredients from your fridge! 🧊")
fridge_image = "fridge.jpg"  
st.image(fridge_image, use_container_width=True)

def input_section(label):
    return st.text_area(label, "", key=label.replace(" ", "_"))

freezer = input_section("Freezer ⛄️")
fridge_body = input_section("Fridge Body 🍱🍚")
cold_storage = input_section("Cold Storage Area 🍎🥦")
other = input_section("Other ingredients 🧂🥫")

ingredients = ", ".join(filter(None, [cold_storage, freezer, fridge_body, other]))

dietary = st.selectbox("Dietary Restrictions", [
    "None",
    "Vegetarian",
    "Vegan",
    "Gluten-Free",
    "Halal",
    "Kosher",
    "Dairy-Free",
    "Nut-Free",
    "Pescatarian"
])

food_type = st.selectbox("Preferred Food Type", [
    "None",
    "Soup",
    "Noodles",
    "Rice",
    "Salad",
    "Dessert",
    "Sandwich",
    "Baked Goods",
    "One-Pot Meal"
])

if st.button("Generate recipes! 🍰"):
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Cute loading messages
    loading_messages = [
        "🧁 Whipping up something delicious...",
        "🥄 Gathering ingredients...",
        "🍳 Mixing the recipe...",
        "🎨 Adding some sparkles...",
        "✨ Making it extra cute...",
        "🌟 Almost ready..."
    ]
    
    pdfs = []
    recipes = []
    
    # Generate recipes (25% of progress)
    status_text.text(loading_messages[0])
    progress_bar.progress(10)
    recipes = generate_recipes(ingredients, dietary, food_type)
    progress_bar.progress(25)
    
    global recipe_counter
    recipe_counter = 1
    
    # Process each recipe (75% remaining progress)
    progress_per_recipe = 75 / len(recipes) if recipes else 75
    current_progress = 25
    
    for i, recipe in enumerate(recipes):
        status_text.text(loading_messages[min(i+1, len(loading_messages)-1)])
        recipe["image_path"] = f"recipe_image_{i}.png"
        try:
            generate_recipe_image(f"A delicious plate of {recipe['title']}", recipe["image_path"])
        except Exception as e:
            print(f"Error generating image: {e}")
            recipe["image_path"] = None 
        
        recipe["nutrition"] = get_nutrition_info(recipe)
        progress_bar.progress(int(current_progress + progress_per_recipe * 0.3))
        
        recipe["missing_ingredients"] = extract_missing_ingredients(recipe["ingredients"], ingredients)
        progress_bar.progress(int(current_progress + progress_per_recipe * 0.6))
        
        for ing in recipe["missing_ingredients"]:
            add_links(ing)
        pdfs.append(create_pdf(recipe))
        recipe_counter += 1
        current_progress += progress_per_recipe
        progress_bar.progress(int(current_progress))
    
    # Complete the progress
    status_text.text("🎊 Your recipes are ready! 🎉")
    progress_bar.progress(100)
    
    # Display Recipes
    st.subheader("🥪 Your Recipes 🥗")
    
    # Create tabs for each recipe
    tabs = st.tabs([f"Recipe {i+1}" for i in range(len(recipes))])
    
    for i, (tab, recipe) in enumerate(zip(tabs, recipes)):
        with tab:
            st.markdown(f"## {recipe['title']} {get_food_emoji(recipe['title'])}")
            
            if recipe.get("image_path"):
                st.image(recipe["image_path"], use_container_width=True)
            
            # Nutrition Info
            st.markdown("### Nutrition Information")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Calories", recipe['nutrition']['calories'])
            with col2:
                st.metric("Protein", recipe['nutrition']['protein'])
            with col3:
                st.metric("Carbs", recipe['nutrition']['carbohydrates'])
            with col4:
                st.metric("Fat", recipe['nutrition']['fat'])
            
            # Ingredients
            st.markdown("### Ingredients")
            for ing in recipe['ingredients']:
                st.write(f"• {ing['name']} - {ing['weight']}")
            
            # Missing Ingredients
            st.markdown("### Ingredients to purchase")
            for ing in recipe['missing_ingredients']:
                cost = ing['cost']
                text_body = f"• {ing['name'].capitalize()}: {cost}"
                st.write(text_body.replace("$","\$"))
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.link_button("Buy at NTUC", ing['ntuc'])
                with col2:
                    st.link_button("Buy at Sheng Siong", ing['shengsiong'])
                with col3:
                    st.link_button("Buy at Cold Storage", ing['coldstorage'])
            
            # Steps
            st.markdown("### Steps")
            for step in recipe['steps']:
                st.write(f"{step}")
            
            # PDF Download
            if pdfs[i]:
                with open(pdfs[i], 'rb') as pdf_file:
                    pdf_bytes = pdf_file.read()
                st.download_button(
                    "Download Recipe as PDF 🎀",
                    data=pdf_bytes,
                    file_name=f"recipe_{i+1}.pdf",
                    mime="application/pdf",
                    key=f"pdf_download_{i}",
                    on_click="ignore" 
                )
    
    st.balloons()
    print("complete!")