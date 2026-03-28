from google import genai
from config import Config
import re
import json

client = genai.Client(api_key=Config.GEMINI_API_KEY)


def clean_response(text):
    text = re.sub(r'```(?:[a-zA-Z]*)?\n?(.*?)```', r'\1', text, flags=re.DOTALL)
    return text.strip()


def analyze_meal_image(image_bytes, goal):
    print(f"[AI] Analyzing meal image for goal: {goal}")
    
    prompt = f"""
    You are an expert sports nutritionist and AI vision model. Analyze the uploaded image of a meal.
    1. Identify the name of the overall dish.
    2. Identify the specific food items/ingredients and estimate their approximate portion sizes.
    3. For each specific food item, estimate its calories and macros.
    4. Calculate the total calories, protein (g), carbs (g), and fats (g) for the entire meal.
    5. Compare this overall nutritional profile against the user's fitness goal: "{goal}".
    6. Provide exactly 2 short, actionable improvement tips.
    
    Return exactly a JSON object (no markdown, no backticks, just raw JSON) with this exact structure:
    {{
        "dish_name": "Example Dish Name",
        "items": [
            {{"name": "Grilled Chicken (150g)", "calories": 250, "protein": 35, "carbs": 0, "fats": 5}},
            {{"name": "White Rice (100g)", "calories": 130, "protein": 2, "carbs": 28, "fats": 0}}
        ],
        "total": {{"calories": 380, "protein": 37, "carbs": 28, "fats": 5}},
        "alignment_status": "Good",
        "tips": ["Tip 1...", "Tip 2..."]
    }}
    """
    try:
        from google.genai import types
        try:
            image_part = types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg')
        except Exception:
            image_part = {"mime_type": "image/jpeg", "data": image_bytes}
            
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[prompt, image_part],
            config={"response_mime_type": "application/json"}
        )
        
        raw = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(raw)
        return data
    except Exception as e:
        print(f"[AI] Image analysis error (using fallback): {e}")
        import random
        fallbacks = [
            {
                "dish_name": "(Fallback) Grilled Chicken & Roasted Veggies",
                "items": [
                    {"name": "Grilled Chicken Breast (150g)", "calories": 248, "protein": 46, "carbs": 0, "fats": 5},
                    {"name": "Sweet Potato (100g)", "calories": 86, "protein": 2, "carbs": 20, "fats": 0},
                    {"name": "Steamed Broccoli (80g)", "calories": 28, "protein": 3, "carbs": 6, "fats": 0},
                    {"name": "Olive Oil Drizzle (1 tbsp)", "calories": 119, "protein": 0, "carbs": 0, "fats": 14}
                ],
                "total": {"calories": 481, "protein": 51, "carbs": 26, "fats": 19},
                "alignment_status": "Moderate",
                "tips": [
                    f"Double-check your portion sizes align tightly with your {goal} objective.",
                    "Ensure your protein source is lean (like grilled chicken or tofu) to keep saturated fats low."
                ]
            },
            {
                "dish_name": "(Fallback) Steak & Asparagus Dinner",
                "items": [
                    {"name": "Grilled Sirloin Steak (200g)", "calories": 414, "protein": 54, "carbs": 0, "fats": 20},
                    {"name": "Roasted Asparagus (150g)", "calories": 40, "protein": 4, "carbs": 7, "fats": 0},
                    {"name": "Mashed Potatoes (150g)", "calories": 160, "protein": 3, "carbs": 26, "fats": 5}
                ],
                "total": {"calories": 614, "protein": 61, "carbs": 33, "fats": 25},
                "alignment_status": "Good",
                "tips": [
                    "Great source of protein for muscle synthesis.",
                    "Consider swapping the mashed potatoes for cauliflower mash to reduce carbs."
                ]
            },
            {
                "dish_name": "(Fallback) Avocado Toast & Eggs",
                "items": [
                    {"name": "Whole Wheat Bread (2 slices)", "calories": 160, "protein": 8, "carbs": 28, "fats": 2},
                    {"name": "Mashed Avocado (100g)", "calories": 160, "protein": 2, "carbs": 9, "fats": 15},
                    {"name": "Poached Eggs (2 large)", "calories": 144, "protein": 12, "carbs": 1, "fats": 10}
                ],
                "total": {"calories": 464, "protein": 22, "carbs": 38, "fats": 27},
                "alignment_status": "Not Ideal",
                "tips": [
                    "High in healthy fats, but be mindful of total calorie density.",
                    f"To better align with your {goal} goal, use egg whites instead of whole eggs to drop fats."
                ]
            }
        ]
        return random.choice(fallbacks)


def calculate_bmi(weight, height):
    h = float(height) / 100
    return round(float(weight) / (h ** 2), 1)


def bmi_status(bmi):
    if bmi < 18.5: return "Underweight"
    elif bmi < 25:  return "Normal weight"
    elif bmi < 30:  return "Overweight"
    else:           return "Obese"


def calculate_calories(age, gender, height, weight, activity):
    w, h, a = float(weight), float(height), float(age)
    if str(gender).lower() == "male":
        bmr = 10 * w + 6.25 * h - 5 * a + 5
    else:
        bmr = 10 * w + 6.25 * h - 5 * a - 161
    multipliers = {
        "sedentary": 1.2, "light": 1.375, "moderate": 1.55,
        "active": 1.725, "very active": 1.9
    }
    return round(bmr * multipliers.get(str(activity).lower(), 1.2))


def target_calories(maintenance, goal):
    g = str(goal).lower()
    if g == "lose":   return maintenance - 500
    elif g == "gain": return maintenance + 400
    return maintenance


def macro_split(calories, goal):
    g = str(goal).lower()
    if g == "lose":
        p = round(calories * 0.35 / 4)
        f = round(calories * 0.30 / 9)
        c = round(calories * 0.35 / 4)
    elif g == "gain":
        p = round(calories * 0.30 / 4)
        f = round(calories * 0.25 / 9)
        c = round(calories * 0.45 / 4)
    else:
        p = round(calories * 0.30 / 4)
        f = round(calories * 0.30 / 9)
        c = round(calories * 0.40 / 4)
    return p, f, c


def fitness_level(activity):
    a = str(activity).lower()
    if a in ("sedentary", "light"):   return "beginner"
    elif a == "moderate":             return "intermediate"
    else:                             return "advanced"


def parse_plan(text):
    data = {"Breakfast": "", "Lunch": "", "Dinner": "", "Snacks": "", "Tips": ""}
    current_key = None
    for line in text.splitlines():
        clean_line = line.strip()
        if not clean_line:
            continue
        found_key = False
        for key in data:
            if re.search(rf'^(?:\*|#|\s)*{key}(?:\*|\s|:)*$', clean_line, re.IGNORECASE):
                current_key = key
                data[key] = ""
                found_key = True
                break
        if not found_key and current_key:
            data[current_key] += clean_line + "\n"
    return data


def parse_weekly_plan(text):
    text = clean_response(text)
    weekly = {}
    current_day = None
    buffer = ""
    for line in text.splitlines():
        clean_line = line.strip()
        if not clean_line:
            continue
        if re.search(r'^(?:\*|#|\s)*Day\s+\d+(?:\*|\s|:)*$', clean_line, re.IGNORECASE):
            if current_day and buffer:
                weekly[current_day] = parse_plan(buffer)
                buffer = ""
            current_day = clean_line.strip('*# ')
        else:
            buffer += clean_line + "\n"
    if current_day and buffer:
        weekly[current_day] = parse_plan(buffer)
    return weekly


def build_user_context(age, gender, height, weight, goal, diet, activity, cuisine="Standard"):
    bmi     = calculate_bmi(weight, height)
    bmi_cat = bmi_status(bmi)
    maint   = calculate_calories(age, gender, height, weight, activity)
    tgt     = target_calories(maint, goal)
    pro, fat, carb = macro_split(tgt, goal)
    level   = fitness_level(activity)

    cuisine_note = f"{cuisine} cuisine" if cuisine and cuisine.lower() != "standard" else "standard international cuisine"

    goal_map = {
        "lose":     "fat loss (caloric deficit)",
        "gain":     "muscle gain (caloric surplus)",
        "maintain": "weight maintenance (balanced nutrition)",
    }
    goal_desc = goal_map.get(str(goal).lower(), str(goal))

    bkf = round(tgt * 0.25)
    lch = round(tgt * 0.35)
    din = round(tgt * 0.28)
    snk = round(tgt * 0.12)

    context = (
        f"Age: {age} | Gender: {gender} | Height: {height}cm | Weight: {weight}kg\n"
        f"BMI: {bmi} ({bmi_cat}) | Goal: {goal_desc} | Diet: {diet}\n"
        f"Activity: {activity} ({level} fitness) | {cuisine_note}\n"
        f"Maintenance kcal: {maint} | TARGET kcal: {tgt}\n"
        f"Macros: {pro}g protein / {fat}g fat / {carb}g carbs\n"
        f"Meal calorie split — Breakfast: {bkf} kcal | Lunch: {lch} kcal | Dinner: {din} kcal | Snacks: {snk} kcal"
    )
    return context, bmi, bmi_cat, maint, tgt, pro, fat, carb, level, bkf, lch, din, snk


def generate_meal_plan(age, gender, height, weight, goal, diet, activity, cuisine="Standard"):
    ctx, bmi, bmi_cat, maint, tgt, pro, fat, carb, level, bkf, lch, din, snk = \
        build_user_context(age, gender, height, weight, goal, diet, activity, cuisine)

    print(f"[AI] Generating meal plan | BMI:{bmi} ({bmi_cat}) | Target:{tgt} kcal | Goal:{goal} | Diet:{diet}")

    if bmi_cat == "Obese":
        bmi_rule = "STRICT: low-calorie, high-fibre, low-glycaemic foods only. Absolutely NO fried, sugary, or ultra-processed items."
    elif bmi_cat == "Overweight":
        bmi_rule = "STRICT: moderate-calorie, high-protein, high-fibre meals. Avoid refined carbs, sugary drinks, and fried foods."
    elif bmi_cat == "Underweight":
        bmi_rule = "STRICT: calorie-dense, nutrient-rich foods. Include healthy fats (avocado, nuts, olive oil), complex carbs, and protein at every meal."
    else:
        bmi_rule = "Balanced, nutritious meals. Align portion sizes with the goal."

    cuisine_str = cuisine if cuisine and cuisine.lower() != "standard" else "standard international"

    prompt = f"""You are a certified dietitian creating a PERSONALIZED 1-day meal plan.

USER PROFILE:
{ctx}

IMPORTANT RULES — follow exactly:
1. This person is {bmi_cat} (BMI {bmi}). {bmi_rule}
2. Total plan must be as close to {tgt} kcal as possible (NOT a generic 2000-kcal plan).
3. Breakfast must be ~{bkf} kcal | Lunch ~{lch} kcal | Dinner ~{din} kcal | Snacks ~{snk} kcal.
4. Include exact weights (grams, ml, or pieces) for EVERY food item — no vague quantities.
5. Diet: {diet} — do not include any forbidden foods.
6. Cuisine: {cuisine_str} — use appropriate regional foods.
7. Goal is {goal} — adjust food choices accordingly.
8. Use ONLY these exact section headings on their own line, nothing else on that line:
   Breakfast:
   Lunch:
   Dinner:
   Snacks:
   Tips:
9. Under each heading, list items as bullet points starting with "- ".
10. For Tips, give 2 specific tips relevant to a {bmi_cat} person aiming to {goal} weight.

OUTPUT FORMAT EXAMPLE (use identical format):
Breakfast:
- Rolled oats (80g cooked) with skimmed milk (150ml) and sliced banana (1 medium)
- Black coffee or green tea

Lunch:
- Grilled chicken breast (150g) with brown rice (100g cooked) and steamed broccoli (120g)
- Mixed salad with lemon dressing

Dinner:
- Baked salmon fillet (130g) with roasted sweet potato (120g) and green beans (100g)

Snacks:
- Apple (1 medium) with 10 almonds
- Low-fat Greek yogurt (150g)

Tips:
- Tip specific to BMI category and goal
- Another specific actionable tip

NO introduction, conclusion, or extra text. Start directly with "Breakfast:".
"""

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        raw = response.text.strip()
        print(f"[AI] Response received ({len(raw)} chars). First 120: {raw[:120]}")
        parsed = parse_plan(raw)
        if not any(parsed.values()):
            print("[AI] WARNING: parse_plan returned all-empty dict. Raw response format may not match parser.")
            print(f"[AI] First 400 chars of raw: {raw[:400]}")
        return parsed
    except Exception as e:
        print(f"[AI] ERROR in generate_meal_plan: {e}")

    if bmi_cat in ("Obese", "Overweight"):
        return {
            "Breakfast": f"- Oats (60g dry) with water and berries (100g) | ~{bkf} kcal target\n- Green tea (no sugar)",
            "Lunch": f"- Grilled chicken breast (150g) with 1/2 cup brown rice and salad | ~{lch} kcal target",
            "Dinner": f"- Steamed fish (130g) with roasted vegetables (200g), no oil | ~{din} kcal target",
            "Snacks": f"- Apple (1 medium) + 10 almonds | ~{snk} kcal target",
            "Tips": f"- Target {tgt} kcal daily (your maintenance is {maint} kcal)\n- Choose high-fibre foods to stay full on fewer calories"
        }
    elif bmi_cat == "Underweight":
        return {
            "Breakfast": f"- Peanut butter (2 tbsp) on whole-grain toast (2 slices) + banana | ~{bkf} kcal target",
            "Lunch": f"- Brown rice (150g cooked) + lentil curry (200g) + avocado (1/2) | ~{lch} kcal target",
            "Dinner": f"- Chicken thigh (180g) with sweet potato (150g) and olive oil | ~{din} kcal target",
            "Snacks": f"- Handful of mixed nuts (40g) + full-fat milk (300ml) | ~{snk} kcal target",
            "Tips": f"- Eat {tgt} kcal daily to gain weight steadily\n- Add healthy fats (nuts, seeds, avocado) to boost calories"
        }
    return {
        "Breakfast": f"- Eggs (3 scrambled) with spinach (80g) and 1 slice whole-grain toast | ~{bkf} kcal target",
        "Lunch": f"- Grilled chicken (150g) with quinoa (80g), cucumber, and tomatoes | ~{lch} kcal target",
        "Dinner": f"- Baked salmon (140g) with asparagus (120g) and half sweet potato | ~{din} kcal target",
        "Snacks": f"- Greek yogurt (150g) + 1 apple | ~{snk} kcal target",
        "Tips": f"- Aim for {tgt} kcal/day to {goal} weight effectively\n- Spread meals 3-4 hours apart for stable energy"
    }



def replace_single_meal(meal_type, age, gender, height, weight, goal, diet, activity, cuisine="Standard", variation=1):
    ctx, bmi, bmi_cat, maint, tgt, pro, fat, carb, level, bkf, lch, din, snk = \
        build_user_context(age, gender, height, weight, goal, diet, activity, cuisine)

    cal_map = {"Breakfast": bkf, "Lunch": lch, "Dinner": din, "Snacks": snk}
    cal_target = cal_map.get(meal_type, round(tgt * 0.25))
    cuisine_str = cuisine if cuisine and cuisine.lower() != "standard" else "standard international"

    ordinals = {1:"1st",2:"2nd",3:"3rd"}
    ordinal = ordinals.get(variation, f"{variation}th")

    print(f"[AI] Replacing {meal_type} #{variation} | Target:{cal_target} kcal | Diet:{diet} | Cuisine:{cuisine_str}")

    variety_note = ""
    if variation == 1:
        variety_note = "Suggest a fresh, creative option."
    elif variation == 2:
        variety_note = "This is the 2nd alternative — use COMPLETELY DIFFERENT ingredients from what you would normally suggest first. Think less conventional but still healthy."
    elif variation == 3:
        variety_note = "This is the 3rd alternative — be even more creative. Use different protein sources, grains, or cooking methods than typical suggestions."
    else:
        variety_note = f"This is alternative #{variation}. The user has already seen {variation-1} options. Give something truly unique and varied — different protein, different carb source, different flavour profile. Avoid eggs, chicken breast, oats, and salmon if they appear in earlier common suggestions."

    prompt = f"""You are a dietitian. Generate the {ordinal} alternative {meal_type} for this person.

USER: {ctx}

Target: ~{cal_target} kcal for this {meal_type}.
Diet: {diet} | BMI: {bmi} ({bmi_cat}) | Goal: {goal} | Cuisine: {cuisine_str}

{variety_note}

Rules:
- Maintain the same calorie target (~{cal_target} kcal)
- Include exact weights (grams, ml, or pieces)
- 2-3 food items only
- Start directly with "- ", no introductory text
"""
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"[AI] Replace meal error: {e}")
        if meal_type == "Breakfast":
            fallbacks = [
                f"- Scrambled eggs (2) on wholewheat toast (1 slice) + 1/2 avocado | ~{cal_target} kcal",
                f"- High-protein Greek yogurt (200g) + honey (1 tsp) + mixed berries (80g) | ~{cal_target} kcal",
                f"- Protein smoothie (1 scoop whey, 200ml almond milk, 1/2 banana) | ~{cal_target} kcal"
            ]
        elif meal_type == "Lunch":
            fallbacks = [
                f"- Grilled turkey breast (150g) + quinoa (100g) + vinaigrette | ~{cal_target} kcal",
                f"- Tuna salad sandwich (wholewheat bread, 1/2 can tuna, light mayo) | ~{cal_target} kcal",
                f"- Baked tofu (150g) wrap with mixed greens and hummus | ~{cal_target} kcal"
            ]
        elif meal_type == "Dinner":
            fallbacks = [
                f"- Lean steak (150g) + asparagus (100g) + roasted potatoes (100g) | ~{cal_target} kcal",
                f"- Chicken fajita bowl (150g chicken, bell peppers, 50g black beans) | ~{cal_target} kcal",
                f"- Baked cod fillet (180g) with lemon, zucchini squash, and brown rice | ~{cal_target} kcal"
            ]
        else:
            fallbacks = [
                f"- Rice cakes (2) with peanut butter (1 tbsp) | ~{cal_target} kcal",
                f"- Handful of edamame (100g) + string cheese | ~{cal_target} kcal",
                f"- Protein bar (low-sugar) + small apple | ~{cal_target} kcal"
            ]
        return fallbacks[(variation - 1) % len(fallbacks)]



def generate_workout_plan(age, gender, height, weight, goal, activity):
    ctx, bmi, bmi_cat, maint, tgt, pro, fat, carb, level, *_ = \
        build_user_context(age, gender, height, weight, goal, "any", activity)

    print(f"[AI] Generating workout plan | BMI:{bmi} ({bmi_cat}) | Level:{level} | Goal:{goal}")

    if bmi_cat == "Obese":
        bmi_rule = "Low-impact ONLY: walking, cycling, swimming, water aerobics. NO jumping, running, or heavy barbell work. Prioritise joint health."
        structure = "5 cardio/low-impact days + 1 light strength + 1 rest"
    elif bmi_cat == "Overweight":
        bmi_rule = "Moderate-intensity cardio (brisk walking, cycling) + bodyweight and light dumbbell strength. Avoid high-impact plyometrics."
        structure = "3 strength days + 3 cardio days + 1 rest"
    elif bmi_cat == "Underweight":
        bmi_rule = "Focus on progressive strength and hypertrophy. Minimal cardio (max 1 session) to protect calorie surplus."
        structure = "5 strength days (Push/Pull/Legs split) + 1 active recovery + 1 rest"
    else:
        bmi_rule = "Balanced mix of strength and cardio. Progress loads week over week."
        structure = "4 strength days + 2 cardio/HIIT days + 1 rest"

    if level == "beginner":
        intensity_note = "Beginner: simpler compound movements, 3 sets, longer rest (90s). No complex lifts."
    elif level == "advanced":
        intensity_note = "Advanced: compound barbell lifts, 4-5 sets, shorter rest (45-60s), progressive overload."
    else:
        intensity_note = "Intermediate: mix of machines and free weights, 3-4 sets, 60-75s rest."

    prompt = f"""You are a certified personal trainer creating a PERSONALISED 7-day workout plan.

USER PROFILE:
{ctx}

KEY RULES:
1. BMI is {bmi} ({bmi_cat}): {bmi_rule}
2. Fitness level is {level}: {intensity_note}
3. Weekly structure must be: {structure}
4. Goal is {goal} — adjust volume/cardio accordingly.
5. Include 4-6 exercises per training day with exact sets x reps (or duration for cardio).
6. Name each day's focus precisely (e.g. "Upper Body Push", "LISS Cardio 30 min", "Rest & Recovery").

USE EXACTLY THIS FORMAT for all 7 days:

Day 1
Focus: [Name of focus]
- Exercise name (sets x reps or duration)
- Exercise name (sets x reps or duration)

Day 2
Focus: [Name of focus]
- Exercise name (sets x reps or duration)

...continue to Day 7.

NO introduction or conclusion. Start directly with "Day 1".
"""

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        raw = response.text.strip()
        print(f"[AI] Workout response ({len(raw)} chars). First 100: {raw[:100]}")
        return parse_weekly_plan(raw)
    except Exception as e:
        print(f"[AI] Workout ERROR: {e}")

    fallback = {}
    workout_days = [
        {"Focus": "Upper Body Push", "Workout": "- Push-ups (3 x 15)\n- Dumbbell Press (3 x 12)\n- Lateral Raises (3 x 15)\n- Tricep Dips (3 x 12)"},
        {"Focus": "Lower Body Strength", "Workout": "- Squats (3 x 15)\n- Romanian Deadlifts (3 x 12)\n- Lunges (3 x 12 each leg)\n- Calf Raises (3 x 20)"},
        {"Focus": "Cardio & Core", "Workout": "- Brisk Walk 30 min\n- Plank (3 x 45s)\n- Bicycle Crunches (3 x 20)\n- Leg Raises (3 x 15)"},
        {"Focus": "Upper Body Pull", "Workout": "- Dumbbell Rows (3 x 12)\n- Bicep Curls (3 x 12)\n- Face Pulls (3 x 15)\n- Hammer Curls (3 x 12)"},
        {"Focus": "Full Body Strength", "Workout": "- Goblet Squats (3 x 12)\n- Overhead Press (3 x 10)\n- Kettlebell Swings (3 x 15)\n- Farmer's Carry (3 x 30m)"},
        {"Focus": "HIIT / Cardio", "Workout": "- Jump Squats (40s on, 20s off x 4)\n- Mountain Climbers (40s on, 20s off x 4)\n- High Knees (40s on, 20s off x 4)\n- Burpees (40s on, 20s off x 4)"},
        {"Focus": "Rest & Recovery", "Workout": "- Full Rest Day\n- Foam Rolling (15 min)\n- Light Stretching (10 min)"},
    ]
    for i, day_data in enumerate(workout_days):
        fallback[f"Day {i + 1}"] = day_data
    return fallback

def generate_weekly_plan(age, gender, height, weight, goal, diet, activity, cuisine="Standard"):
    ctx, *_ = build_user_context(age, gender, height, weight, goal, diet, activity, cuisine)
    return {}
