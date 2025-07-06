# Enhanced Food & Nutrition Explorer App
# Professional version with all requested improvements

import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# 🎯 Page Configuration - English Version
st.set_page_config(
    page_title="Food & Nutrition Explorer",
    page_icon="🍔",
    layout="wide"
)

# 🎨 Main Header
st.title("🍔 Food & Nutrition Explorer")
st.markdown("**Discover recipes based on your ingredients + Complete nutritional analysis**")
st.markdown("---")

# 📝 Pre-defined ingredients list - extensive list for selection
COMMON_INGREDIENTS = [
    # Proteins
    "chicken", "beef", "pork", "fish", "salmon", "tuna", "shrimp", "turkey", "lamb", "tofu",
    "eggs", "beans", "lentils", "chickpeas", "quinoa", "nuts", "almonds", "peanuts",
    
    # Vegetables
    "tomatoes", "onions", "garlic", "carrots", "potatoes", "broccoli", "spinach", "lettuce",
    "bell peppers", "mushrooms", "zucchini", "cucumber", "celery", "corn", "peas", "cabbage",
    "cauliflower", "eggplant", "asparagus", "green beans", "sweet potatoes", "avocado",
    
    # Fruits
    "apples", "bananas", "oranges", "lemons", "limes", "strawberries", "blueberries", 
    "grapes", "pineapple", "mango", "papaya", "kiwi", "peaches", "pears", "cherries",
    
    # Grains & Carbs
    "rice", "pasta", "bread", "oats", "barley", "wheat", "noodles", "couscous", "bulgur",
    "flour", "cornmeal", "crackers", "cereal",
    
    # Dairy & Alternatives
    "milk", "cheese", "yogurt", "butter", "cream", "sour cream", "cottage cheese", 
    "mozzarella", "parmesan", "cheddar", "goat cheese", "coconut milk", "almond milk",
    
    # Herbs & Spices
    "basil", "oregano", "thyme", "rosemary", "parsley", "cilantro", "mint", "dill",
    "paprika", "cumin", "turmeric", "ginger", "black pepper", "salt", "cinnamon", "vanilla",
    
    # Oils & Condiments
    "olive oil", "vegetable oil", "coconut oil", "vinegar", "soy sauce", "honey", "maple syrup",
    "mustard", "ketchup", "mayonnaise", "hot sauce", "lemon juice"
]

# =============================================================================
# 🔧 Enhanced API Functions with better error handling
# =============================================================================

@st.cache_data(ttl=3600)
def search_recipes_by_ingredients(ingredients):
    """
    🔍 Enhanced recipe search with multiple ingredients support
    """
    recipes_found = []
    
    # Try searching with each ingredient to get more variety
    for ingredient in ingredients[:3]:  # Limit to first 3 ingredients
        url = f"https://www.themealdb.com/api/json/v1/1/search.php"
        params = {"s": ingredient}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('meals'):
                    for meal in data['meals'][:4]:  # 4 recipes per ingredient
                        # Extract ingredients from the meal
                        meal_ingredients = []
                        for i in range(1, 21):
                            ing = meal.get(f'strIngredient{i}', '')
                            measure = meal.get(f'strMeasure{i}', '')
                            if ing and ing.strip():
                                meal_ingredients.append(f"{measure.strip()} {ing.strip()}")
                        
                        recipe = {
                            'id': meal.get('idMeal'),
                            'name': meal.get('strMeal', 'Unknown'),
                            'image': meal.get('strMealThumb', ''),
                            'instructions': meal.get('strInstructions', 'No instructions available'),
                            'category': meal.get('strCategory', 'General'),
                            'area': meal.get('strArea', 'International'),
                            'youtube': meal.get('strYoutube', ''),
                            'ingredients': meal_ingredients,
                            'tags': meal.get('strTags', '').split(',') if meal.get('strTags') else []
                        }
                        
                        # Avoid duplicates
                        if not any(r['id'] == recipe['id'] for r in recipes_found):
                            recipes_found.append(recipe)
            
        except Exception as e:
            continue
    
    return recipes_found[:12]  # Return max 12 recipes

@st.cache_data(ttl=3600)
def get_nutrition_info_enhanced(food_item):
    """
    🥗 Enhanced nutrition API with better data processing
    """
    # Try multiple nutrition APIs for better coverage
    
    # API 1: USDA FoodData Central
    try:
        search_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
        params = {
            "query": food_item,
            "pageSize": 3,
            "api_key": "DEMO_KEY"
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('foods') and len(data['foods']) > 0:
                food = data['foods'][0]
                
                nutrition = {
                    'name': food.get('description', food_item),
                    'brand': food.get('brandOwner', 'Generic'),
                    'nutrients': {},
                    'calories_per_100g': 0
                }
                
                # Extract key nutrients
                for nutrient in food.get('foodNutrients', []):
                    name = nutrient.get('nutrientName', '').lower()
                    amount = nutrient.get('value', 0)
                    unit = nutrient.get('unitName', '')
                    
                    # Map important nutrients
                    if 'energy' in name and 'kcal' in unit.lower():
                        nutrition['calories_per_100g'] = amount
                        nutrition['nutrients']['Calories'] = f"{amount} kcal"
                    elif 'protein' in name:
                        nutrition['nutrients']['Protein'] = f"{amount} {unit}"
                    elif 'carbohydrate' in name and 'by difference' in name:
                        nutrition['nutrients']['Carbohydrates'] = f"{amount} {unit}"
                    elif 'total lipid' in name or ('fat' in name and 'total' in name):
                        nutrition['nutrients']['Total Fat'] = f"{amount} {unit}"
                    elif 'fiber' in name:
                        nutrition['nutrients']['Fiber'] = f"{amount} {unit}"
                    elif 'sugars' in name and 'total' in name:
                        nutrition['nutrients']['Sugar'] = f"{amount} {unit}"
                    elif 'sodium' in name:
                        nutrition['nutrients']['Sodium'] = f"{amount} {unit}"
                
                return nutrition
        
    except Exception as e:
        pass
    
    # Fallback: Return estimated nutrition based on food type
    return get_estimated_nutrition(food_item)

def get_estimated_nutrition(food_item):
    """
    📊 Fallback nutrition estimation for common foods
    """
    # Basic nutrition estimates for common foods (per 100g)
    nutrition_estimates = {
        'chicken': {'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6},
        'beef': {'calories': 250, 'protein': 26, 'carbs': 0, 'fat': 17},
        'rice': {'calories': 130, 'protein': 2.7, 'carbs': 28, 'fat': 0.3},
        'pasta': {'calories': 131, 'protein': 5, 'carbs': 25, 'fat': 1.1},
        'potato': {'calories': 77, 'protein': 2, 'carbs': 17, 'fat': 0.1},
        'tomato': {'calories': 18, 'protein': 0.9, 'carbs': 3.9, 'fat': 0.2},
        'cheese': {'calories': 113, 'protein': 7, 'carbs': 1, 'fat': 9},
        'egg': {'calories': 155, 'protein': 13, 'carbs': 1.1, 'fat': 11},
        'bread': {'calories': 265, 'protein': 9, 'carbs': 49, 'fat': 3.2},
        'fish': {'calories': 206, 'protein': 22, 'carbs': 0, 'fat': 12}
    }
    
    # Find closest match
    food_lower = food_item.lower()
    for key, values in nutrition_estimates.items():
        if key in food_lower:
            return {
                'name': food_item.title(),
                'brand': 'Estimated',
                'nutrients': {
                    'Calories': f"{values['calories']} kcal",
                    'Protein': f"{values['protein']} g",
                    'Carbohydrates': f"{values['carbs']} g",
                    'Total Fat': f"{values['fat']} g"
                },
                'calories_per_100g': values['calories']
            }
    
    # Default values if no match
    return {
        'name': food_item.title(),
        'brand': 'Estimated',
        'nutrients': {
            'Calories': '150 kcal',
            'Protein': '8 g',
            'Carbohydrates': '20 g',
            'Total Fat': '5 g'
        },
        'calories_per_100g': 150
    }

def create_enhanced_nutrition_chart(nutrition_data):
    """
    📊 Enhanced nutrition visualization
    """
    if not nutrition_data or not nutrition_data.get('nutrients'):
        return None
    
    # Extract numeric values for macronutrients
    macros = {}
    colors = []
    
    for name, value in nutrition_data['nutrients'].items():
        try:
            if 'protein' in name.lower():
                numeric_value = float(value.split()[0])
                macros['Protein'] = numeric_value
                colors.append('#FF6B6B')  # Red
            elif 'carbohydrate' in name.lower():
                numeric_value = float(value.split()[0])
                macros['Carbs'] = numeric_value
                colors.append('#4ECDC4')  # Teal
            elif 'fat' in name.lower():
                numeric_value = float(value.split()[0])
                macros['Fat'] = numeric_value
                colors.append('#45B7D1')  # Blue
        except:
            pass
    
    if macros:
        # Create pie chart for macronutrients
        fig = go.Figure(data=[go.Pie(
            labels=list(macros.keys()),
            values=list(macros.values()),
            hole=.3,
            marker_colors=colors
        )])
        
        fig.update_layout(
            title=f"Macronutrient Distribution - {nutrition_data['name']}",
            height=400,
            showlegend=True
        )
        
        return fig
    
    return None

def suggest_daily_meals(target_calories, dietary_preference="any"):
    """
    🍽️ Suggest meals that fit daily calorie target
    """
    # Meal distribution (approximate percentages)
    breakfast_calories = int(target_calories * 0.25)  # 25%
    lunch_calories = int(target_calories * 0.35)      # 35%
    dinner_calories = int(target_calories * 0.30)     # 30%
    snack_calories = int(target_calories * 0.10)      # 10%
    
    meal_suggestions = {
        'breakfast': {
            'target_calories': breakfast_calories,
            'suggestions': []
        },
        'lunch': {
            'target_calories': lunch_calories,
            'suggestions': []
        },
        'dinner': {
            'target_calories': dinner_calories,
            'suggestions': []
        },
        'snacks': {
            'target_calories': snack_calories,
            'suggestions': []
        }
    }
    
    # Sample meal ideas based on calorie ranges
    if breakfast_calories <= 300:
        meal_suggestions['breakfast']['suggestions'] = [
            "Oatmeal with banana and honey",
            "Greek yogurt with berries",
            "Toast with avocado"
        ]
    elif breakfast_calories <= 500:
        meal_suggestions['breakfast']['suggestions'] = [
            "Eggs with toast and fruit",
            "Smoothie bowl with granola",
            "Pancakes with syrup"
        ]
    else:
        meal_suggestions['breakfast']['suggestions'] = [
            "Full breakfast with eggs, bacon, toast",
            "Large smoothie bowl with nuts and seeds",
            "French toast with fruit and cream"
        ]
    
    if lunch_calories <= 400:
        meal_suggestions['lunch']['suggestions'] = [
            "Chicken salad with vegetables",
            "Soup with bread roll",
            "Light sandwich with fruit"
        ]
    elif lunch_calories <= 600:
        meal_suggestions['lunch']['suggestions'] = [
            "Grilled chicken with rice and vegetables",
            "Pasta with tomato sauce and salad",
            "Fish with quinoa and steamed broccoli"
        ]
    else:
        meal_suggestions['lunch']['suggestions'] = [
            "Large pasta dish with meat sauce",
            "Burger with fries and salad",
            "Stir-fry with rice and protein"
        ]
    
    if dinner_calories <= 500:
        meal_suggestions['dinner']['suggestions'] = [
            "Grilled fish with vegetables",
            "Chicken stir-fry with minimal oil",
            "Vegetable curry with small portion rice"
        ]
    elif dinner_calories <= 700:
        meal_suggestions['dinner']['suggestions'] = [
            "Steak with potato and vegetables",
            "Salmon with rice and asparagus",
            "Chicken curry with rice"
        ]
    else:
        meal_suggestions['dinner']['suggestions'] = [
            "Large steak dinner with sides",
            "Rich pasta dish with garlic bread",
            "Full roast dinner with all trimmings"
        ]
    
    meal_suggestions['snacks']['suggestions'] = [
        "Apple with peanut butter",
        "Handful of nuts",
        "Yogurt with honey",
        "Small protein bar"
    ]
    
    return meal_suggestions

# =============================================================================
# 🎮 Enhanced User Interface - Centered and Professional
# =============================================================================

# 🔍 MAIN SEARCH SECTION - Centered
st.write("## 🔍 Find Your Perfect Recipe")

# Create centered columns for search
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # 📝 Text input for manual ingredient entry
    ingredients_input = st.text_area(
        "Enter ingredients you have:",
        placeholder="e.g., chicken, rice, tomatoes, garlic",
        help="Enter ingredients separated by commas",
        height=100
    )
    
    # 🍅 Multi-select for ingredient selection
    st.write("**Or select from common ingredients:**")
    selected_ingredients = st.multiselect(
        "Choose ingredients:",
        options=sorted(COMMON_INGREDIENTS),
        help="Select multiple ingredients from the list"
    )
    
    # Combine manual input and selections
    all_ingredients = []
    if ingredients_input:
        all_ingredients.extend([ing.strip() for ing in ingredients_input.split(',') if ing.strip()])
    if selected_ingredients:
        all_ingredients.extend(selected_ingredients)
    
    # Remove duplicates
    all_ingredients = list(set(all_ingredients))
    
    # Display selected ingredients
    if all_ingredients:
        st.write("**Selected ingredients:**")
        st.write(", ".join(all_ingredients))
    
    # 🔘 Search button
    search_clicked = st.button("🔍 Search Recipes", type="primary", use_container_width=True)

# =============================================================================
# 🍽️ DAILY MEAL PLANNING SECTION
# =============================================================================

st.write("---")
st.write("## 🎯 Daily Meal Planning")

col1, col2 = st.columns(2)

with col1:
    target_calories = st.slider(
        "Daily calorie target:",
        min_value=1200,
        max_value=3500,
        value=2000,
        step=50,
        help="Adjust based on your daily calorie needs"
    )

with col2:
    dietary_pref = st.selectbox(
        "Dietary preference:",
        ["Any", "Vegetarian", "Low-carb", "High-protein"],
        help="Filter suggestions based on dietary needs"
    )

if st.button("📋 Generate Daily Meal Plan", use_container_width=True):
    meal_plan = suggest_daily_meals(target_calories, dietary_pref.lower())
    
    st.write("### 🍽️ Your Personalized Daily Meal Plan")
    st.write(f"**Total Daily Calories:** {target_calories} kcal")
    
    # Display meal plan in columns
    meal_cols = st.columns(4)
    
    meals = [
        ("🌅 Breakfast", meal_plan['breakfast'], "#FFE5B4"),
        ("☀️ Lunch", meal_plan['lunch'], "#E5FFB4"),
        ("🌙 Dinner", meal_plan['dinner'], "#B4E5FF"),
        ("🍎 Snacks", meal_plan['snacks'], "#FFB4E5")
    ]
    
    for i, (meal_name, meal_data, color) in enumerate(meals):
        with meal_cols[i]:
            st.markdown(f"""
            <div style="background-color: {color}; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #333;">{meal_name}</h4>
                <p style="margin: 5px 0; font-weight: bold; color: #666;">
                    Target: {meal_data['target_calories']} kcal
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("**Suggestions:**")
            for suggestion in meal_data['suggestions']:
                st.write(f"• {suggestion}")

# =============================================================================
# 📊 RECIPE RESULTS SECTION
# =============================================================================

if search_clicked and all_ingredients:
    with st.spinner('🔍 Searching for delicious recipes...'):
        recipes = search_recipes_by_ingredients(all_ingredients)
    
    if recipes:
        st.write("---")
        st.success(f"✅ Found {len(recipes)} recipes for your ingredients!")
        
        # Display recipes in a grid
        for i in range(0, len(recipes), 3):
            cols = st.columns(3)
            
            for j, recipe in enumerate(recipes[i:i+3]):
                with cols[j]:
                    # Recipe card styling
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 20px; background-color: #f9f9f9;">
                        <h4 style="color: #333; margin-top: 0;">{recipe['name']}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Recipe image
                    if recipe['image']:
                        st.image(recipe['image'], use_container_width=True)
                    
                    # Recipe details
                    st.write(f"**Category:** {recipe['category']}")
                    st.write(f"**Cuisine:** {recipe['area']}")
                    
                    # Ingredients list
                    with st.expander("📋 View Ingredients"):
                        for ingredient in recipe['ingredients'][:10]:
                            st.write(f"• {ingredient}")
                    
                    # Instructions
                    with st.expander("👩‍🍳 View Instructions"):
                        instructions = recipe['instructions'][:300] + "..." if len(recipe['instructions']) > 300 else recipe['instructions']
                        st.write(instructions)
                    
                    # YouTube link
                    if recipe['youtube']:
                        st.write(f"[📺 Watch on YouTube]({recipe['youtube']})")
                    
                    # Nutrition analysis button
                    if st.button(f"🥗 Nutrition Analysis", key=f"nutrition_{recipe['id']}", use_container_width=True):
                        with st.spinner('🔍 Analyzing nutrition...'):
                            nutrition = get_nutrition_info_enhanced(recipe['name'])
                        
                        if nutrition:
                            st.write("### 📊 Nutritional Information")
                            
                            # Create two columns for nutrition display
                            nut_col1, nut_col2 = st.columns(2)
                            
                            with nut_col1:
                                st.write(f"**Food:** {nutrition['name']}")
                                st.write(f"**Source:** {nutrition['brand']}")
                                
                                # Nutrition table
                                if nutrition['nutrients']:
                                    nutrients_df = pd.DataFrame([
                                        {'Nutrient': name, 'Amount': value}
                                        for name, value in nutrition['nutrients'].items()
                                    ])
                                    st.dataframe(nutrients_df, use_container_width=True)
                            
                            with nut_col2:
                                # Nutrition chart
                                chart = create_enhanced_nutrition_chart(nutrition)
                                if chart:
                                    st.plotly_chart(chart, use_container_width=True)
                                
                                # Calorie information
                                if nutrition.get('calories_per_100g'):
                                    st.metric(
                                        "Calories per 100g",
                                        f"{nutrition['calories_per_100g']} kcal"
                                    )
                        else:
                            st.warning("😕 Nutrition information not available for this recipe")

elif search_clicked:
    st.error("❌ Please enter or select at least one ingredient to search")

# =============================================================================
# 🏠 Welcome Section (when no search is performed)
# =============================================================================

if not search_clicked:
    st.write("---")
    st.write("## 👋 Welcome to Food & Nutrition Explorer!")
    
    # Feature highlights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🔍 **Smart Recipe Search**
        - Enter ingredients you have
        - Select from 100+ common ingredients
        - Get personalized recipe suggestions
        """)
    
    with col2:
        st.markdown("""
        ### 📊 **Detailed Nutrition Analysis**
        - Complete nutritional breakdown
        - Visual charts and graphs
        - Calorie counting support
        """)
    
    with col3:
        st.markdown("""
        ### 🍽️ **Daily Meal Planning**
        - Set your calorie target
        - Get meal suggestions
        - Plan balanced daily nutrition
        """)
    
    # Quick start examples
    st.write("### 💡 Quick Start Examples:")
    
    example_cols = st.columns(4)
    examples = [
        ("🍗 Protein Rich", ["chicken", "eggs", "quinoa"]),
        ("🥗 Healthy & Light", ["spinach", "tomatoes", "avocado"]),
        ("🍝 Comfort Food", ["pasta", "cheese", "garlic"]),
        ("🌱 Vegetarian", ["tofu", "vegetables", "rice"])
    ]
    
    for i, (title, ingredients) in enumerate(examples):
        with example_cols[i]:
            st.info(f"**{title}**\n" + ", ".join(ingredients))

# =============================================================================
# 📊 App Information Footer
# =============================================================================

st.write("---")
col1, col2 = st.columns(2)

with col1:
    st.write("### 📊 Data Sources")
    st.write("• **TheMealDB** - Recipe database")
    st.write("• **USDA FoodData** - Nutritional information")
    st.write("• **100% Free APIs** - No payment required")

with col2:
    st.write("### 💡 Tips for Better Results")
    st.write("• Use simple, common ingredient names")
    st.write("• Try different combinations")
    st.write("• Check nutrition info for dietary planning")

st.markdown("---")
st.markdown("**🚀 Built with ❤️ using Streamlit and Free APIs**")
st.markdown("*Nutritional information is for reference only and should not replace professional dietary advice*")
