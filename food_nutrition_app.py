# Food & Nutrition Explorer App
# Simple version with step-by-step explanations

import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# 🎯 הגדרת העמוד - זה מגדיר איך האפליקציה תיראה
st.set_page_config(
    page_title="Food & Nutrition Explorer",
    page_icon="🍔",
    layout="wide"  # מסך רחב במקום צר
)

# 🎨 כותרת ראשית יפה
st.title("🍔 Food & Nutrition Explorer")
st.markdown("**מחפש מתכונים לפי רכיבים שיש לך בבית + ניתוח תזונתי מלא**")
st.markdown("---")

# 📝 הסבר: כאן אנחנו מגדירים את כל ה-APIs שנשתמש בהם
# השתמשתי ב-APIs חינמיים שלא דורשים מפתח

# =============================================================================
# 🔧 פונקציות API - כל פונקציה מתקשרת עם שירות אחר
# =============================================================================

@st.cache_data(ttl=3600)  # 💾 Cache למשך שעה - חוסך API calls
def search_recipes_by_ingredients(ingredients):
    """
    🔍 חיפוש מתכונים לפי רכיבים באמצעות TheMealDB API
    זה API חינמי לגמרי שלא דורש מפתח
    """
    # 📝 הסבר: נחפש מתכונים שמכילים את הרכיב הראשון ברשימה
    main_ingredient = ingredients[0] if ingredients else "chicken"
    
    # 🌐 כתובת ה-API של TheMealDB - זה השירות שנותן לנו מתכונים
    url = f"https://www.themealdb.com/api/json/v1/1/search.php"
    
    # 📊 פרמטרים לבקשה - מה אנחנו מבקשים מהשירות
    params = {"s": main_ingredient}
    
    try:
        # 📡 שליחת הבקשה לשירות - זה ה-API call בפועל
        response = requests.get(url, params=params, timeout=10)
        
        # ✅ בדיקה שהבקשה הצליחה
        if response.status_code == 200:
            data = response.json()
            
            # 📋 עיבוד הנתונים שחזרו מהשירות
            if data.get('meals'):
                recipes = []
                # 🔄 לולאה על כל מתכון שחזר
                for meal in data['meals'][:6]:  # מגביל ל-6 מתכונים
                    recipes.append({
                        'name': meal.get('strMeal', 'לא ידוע'),
                        'image': meal.get('strMealThumb', ''),
                        'instructions': meal.get('strInstructions', 'אין הוראות'),
                        'category': meal.get('strCategory', 'כללי'),
                        'area': meal.get('strArea', 'בינלאומי'),
                        'youtube': meal.get('strYoutube', ''),
                        # 📝 הסבר: נחלץ רכיבים מהמתכון
                        'ingredients': [
                            meal.get(f'strIngredient{i}', '') 
                            for i in range(1, 21) 
                            if meal.get(f'strIngredient{i}', '')
                        ]
                    })
                return recipes
            else:
                return []
        else:
            st.error(f"❌ שגיאה בשירות המתכונים: {response.status_code}")
            return []
            
    except Exception as e:
        st.error(f"❌ שגיאה בחיבור לשירות המתכונים: {e}")
        return []

@st.cache_data(ttl=3600)  # 💾 Cache למשך שעה
def get_nutrition_info(food_item):
    """
    🥗 קבלת מידע תזונתי מ-USDA FoodData Central API
    זה מסד נתונים ממשלתי אמריקאי - חינמי לחלוטין
    """
    # 🌐 כתובת ה-API של משרד החקלאות האמריקאי
    search_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    
    # 📊 פרמטרים לחיפוש המזון
    params = {
        "query": food_item,
        "pageSize": 5,  # מגביל ל-5 תוצאות
        "api_key": "DEMO_KEY"  # מפתח דמו שעובד למספר מוגבל של בקשות
    }
    
    try:
        # 📡 שליחת בקשה לשירות התזונה
        response = requests.get(search_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # 📋 עיבוד נתוני התזונה
            if data.get('foods') and len(data['foods']) > 0:
                food = data['foods'][0]  # לוקח את התוצאה הראשונה
                
                nutrition = {
                    'name': food.get('description', food_item),
                    'brand': food.get('brandOwner', 'כללי'),
                    'nutrients': {}
                }
                
                # 🔄 חילוץ ערכים תזונתיים
                for nutrient in food.get('foodNutrients', [])[:10]:  # מגביל ל-10 ערכים
                    name = nutrient.get('nutrientName', '')
                    amount = nutrient.get('value', 0)
                    unit = nutrient.get('unitName', '')
                    
                    if name and amount:
                        nutrition['nutrients'][name] = f"{amount} {unit}"
                
                return nutrition
            else:
                return None
        else:
            st.warning(f"⚠️ לא הצלחנו למצוא מידע תזונתי עבור: {food_item}")
            return None
            
    except Exception as e:
        st.warning(f"⚠️ שגיאה בקבלת מידע תזונתי: {e}")
        return None

def create_nutrition_chart(nutrition_data):
    """
    📊 יצירת גרף יפה למידע התזונתי
    זה לוקח את הנתונים ויוצר ויזואליזציה
    """
    if not nutrition_data or not nutrition_data.get('nutrients'):
        return None
    
    # 📝 הסבר: נסנן רק ערכים תזונתיים עיקריים
    main_nutrients = {}
    for name, value in nutrition_data['nutrients'].items():
        # 🔍 מחפש ערכים עיקריים שמעניינים אותנו
        if any(keyword in name.lower() for keyword in ['protein', 'fat', 'carbohydrate', 'fiber', 'sugar', 'sodium']):
            # 🔢 מנסה לחלץ רק את המספר מהטקסט
            try:
                numeric_value = float(value.split()[0])
                main_nutrients[name] = numeric_value
            except:
                pass
    
    # 📊 יצירת גרף עמודות
    if main_nutrients:
        fig = px.bar(
            x=list(main_nutrients.keys()),
            y=list(main_nutrients.values()),
            title=f"ערכים תזונתיים עבור: {nutrition_data['name']}",
            labels={'x': 'רכיבים תזונתיים', 'y': 'כמות'}
        )
        
        # 🎨 עיצוב הגרף
        fig.update_layout(
            xaxis_tickangle=-45,  # זווית של כותרות הX
            height=400
        )
        
        return fig
    
    return None

# =============================================================================
# 🎮 ממשק המשתמש הראשי
# =============================================================================

# 📝 הסבר: כאן מתחיל הממשק שהמשתמש רואה

# 🎯 סייד בר לקלט מהמשתמש
st.sidebar.header("🔍 חיפוש מתכונים")

# 📝 הסבר: תיבת טקסט לכניסת רכיבים
ingredients_input = st.sidebar.text_area(
    "רכיבים שיש לך בבית:",
    placeholder="לדוגמה: עגבניות, גבינה, בצל, פסטה",
    help="הכנס רכיבים מופרדים בפסיקים"
)

# 🔘 כפתור חיפוש
search_clicked = st.sidebar.button("🔍 חפש מתכונים", type="primary")

# 📊 אזור התוצאות הראשי
if search_clicked and ingredients_input:
    # 📝 הסבר: עיבוד הקלט של המשתמש - הפיכת הטקסט לרשימה
    ingredients_list = [ing.strip() for ing in ingredients_input.split(',') if ing.strip()]
    
    if ingredients_list:
        # 🔄 הצגת טוען בזמן החיפוש
        with st.spinner('🔍 מחפש מתכונים מתאימים...'):
            recipes = search_recipes_by_ingredients(ingredients_list)
        
        if recipes:
            st.success(f"✅ נמצאו {len(recipes)} מתכונים!")
            
            # 📝 הסבר: מציג את המתכונים בעמודות יפות
            # נחלק את המסך ל-2 עמודות
            for i in range(0, len(recipes), 2):
                cols = st.columns(2)
                
                # 🔄 לולאה שמציגה עד 2 מתכונים בשורה
                for j, recipe in enumerate(recipes[i:i+2]):
                    with cols[j]:
                        # 🖼️ הצגת תמונת המתכון
                        if recipe['image']:
                            st.image(recipe['image'], width=300)
                        
                        # 📋 פרטי המתכון
                        st.subheader(f"🍽️ {recipe['name']}")
                        st.write(f"**קטגוריה:** {recipe['category']}")
                        st.write(f"**מטבח:** {recipe['area']}")
                        
                        # 🥕 רשימת רכיבים
                        st.write("**רכיבים נדרשים:**")
                        for ingredient in recipe['ingredients'][:8]:  # מגביל ל-8 רכיבים
                            st.write(f"• {ingredient}")
                        
                        # 📺 קישור ליוטיוב אם קיים
                        if recipe['youtube']:
                            st.write(f"[📺 צפה במתכון ביוטיוב]({recipe['youtube']})")
                        
                        # 🔘 כפתור לניתוח תזונתי
                        if st.button(f"🥗 ניתוח תזונתי", key=f"nutrition_{i}_{j}"):
                            # 📝 הסבר: כשלוחצים על הכפתור, מחפש מידע תזונתי
                            with st.spinner('🔍 מחפש מידע תזונתי...'):
                                nutrition = get_nutrition_info(recipe['name'])
                            
                            if nutrition:
                                # 📊 הצגת המידע התזונתי
                                st.write("### 📊 מידע תזונתי")
                                st.write(f"**מוצר:** {nutrition['name']}")
                                st.write(f"**מותג:** {nutrition['brand']}")
                                
                                # 📋 טבלת ערכים תזונתיים
                                if nutrition['nutrients']:
                                    nutrients_df = pd.DataFrame([
                                        {'רכיב תזונתי': name, 'כמות': value}
                                        for name, value in nutrition['nutrients'].items()
                                    ])
                                    st.dataframe(nutrients_df, use_container_width=True)
                                    
                                    # 📊 גרף תזונתי
                                    chart = create_nutrition_chart(nutrition)
                                    if chart:
                                        st.plotly_chart(chart, use_container_width=True)
                            else:
                                st.warning("😕 לא הצלחנו למצוא מידע תזונתי למתכון זה")
                        
                        st.markdown("---")  # קו הפרדה יפה
            
        else:
            # 😕 הודעה כשלא נמצאו מתכונים
            st.warning("😕 לא נמצאו מתכונים עבור הרכיבים שהזנת. נסה רכיבים אחרים.")
            st.info("💡 טיפ: נסה רכיבים פשוטים כמו: עוף, אורז, עגבניות, גבינה")

elif search_clicked:
    # ❌ הודעת שגיאה אם לא הוזנו רכיבים
    st.error("❌ אנא הזן לפחות רכיב אחד לחיפוש")

else:
    # 🏠 מסך בית - מה שמוצג בהתחלה
    st.write("## 👋 ברוכים הבאים!")
    st.write("### איך זה עובד:")
    
    # 📝 הוראות שימוש יפות
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("### 1️⃣ הזן רכיבים")
        st.write("רשום מה יש לך במקרר או בארון")
        st.info("דוגמה: עגבניות, בצל, שום")
    
    with col2:
        st.write("### 2️⃣ חפש מתכונים")
        st.write("לחץ על כפתור החיפוש")
        st.info("נמצא מתכונים מתאימים")
    
    with col3:
        st.write("### 3️⃣ קבל ניתוח תזונתי")
        st.write("לחץ על כפתור הניתוח")
        st.info("קבל מידע על ערכים תזונתיים")
    
    # 📊 דוגמאות להשראה
    st.write("### 💡 רעיונות לחיפוש:")
    examples = [
        "🍗 עוף, אורז, ירקות",
        "🍝 פסטה, עגבניות, בזיליקום", 
        "🥗 חסה, מלפפון, גבינה",
        "🍲 בקר, תפוחי אדמה, גזר",
        "🐟 דג, לימון, שמן זית"
    ]
    
    cols = st.columns(len(examples))
    for i, example in enumerate(examples):
        with cols[i]:
            st.info(example)

# =============================================================================
# 📊 סטטיסטיקות ומידע נוסף
# =============================================================================

# 📝 הסבר: סרגל צידי עם מידע נוסף ושימושי
st.sidebar.markdown("---")
st.sidebar.write("### 📊 מידע על האפליקציה")
st.sidebar.write("🔗 **מקורות המידע:**")
st.sidebar.write("• TheMealDB - מתכונים")
st.sidebar.write("• USDA - מידע תזונתי")
st.sidebar.write("• APIs חינמיים לחלוטין!")

st.sidebar.write("### 💡 טיפים:")
st.sidebar.write("• השתמש ברכיבים פשוטים")
st.sidebar.write("• נסה שמות באנגלית")
st.sidebar.write("• בדוק מספר חיפושים")

# 📝 הסבר: פוטר עם מידע נוסף
st.markdown("---")
st.markdown("**🚀 פותח עם ❤️ בעזרת Streamlit ו-APIs חינמיים**")
st.markdown("*המידע התזונתי להשוואה בלבד ואינו מהווה ייעוץ רפואי*")
