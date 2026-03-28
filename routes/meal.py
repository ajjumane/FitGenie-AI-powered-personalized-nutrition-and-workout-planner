from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from flask_login import login_required, current_user
from utils.ai import (
    generate_meal_plan,
    replace_single_meal,
    generate_workout_plan,
    build_user_context
)
from extensions import db
from flask import send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem
from io import BytesIO
meal_bp = Blueprint("meal", __name__)




def calculate_bmi(weight, height):
    height_m = float(height) / 100
    bmi = float(weight) / (height_m ** 2)
    return round(bmi, 1)


def bmi_status(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 25:
        return "Normal"
    elif 25 <= bmi < 30:
        return "Overweight"
    else:
        return "Obese"


def calculate_calories(age, gender, height, weight, activity):
    if gender.lower() == "male":
        bmr = 10 * float(weight) + 6.25 * float(height) - 5 * float(age) + 5
    else:
        bmr = 10 * float(weight) + 6.25 * float(height) - 5 * float(age) - 161

    activity_multiplier = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very active": 1.9
    }

    return round(bmr * activity_multiplier.get(activity.lower(), 1.2))


def calculate_water_intake(weight):
    return round((float(weight) * 35) / 1000, 2)


def get_user_profile():
    return (
        current_user.age,
        current_user.gender,
        current_user.height,
        current_user.weight,
        current_user.goal,
        current_user.diet,
        current_user.activity,
        current_user.cuisine
    )


# -------------------------
# Routes
# -------------------------

@meal_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@meal_bp.route("/generate", methods=["POST"])
@login_required
def generate():

    # Save profile first time
    if not current_user.age:
        current_user.age = request.form["age"]
        current_user.gender = request.form["gender"]
        current_user.height = request.form["height"]
        current_user.weight = request.form["weight"]
        current_user.goal = request.form["goal"]
        current_user.diet = request.form["diet"]
        current_user.activity = request.form["activity"]
        current_user.cuisine = request.form["cuisine"]
        db.session.commit()

    age, gender, height, weight, goal, diet, activity, cuisine = get_user_profile()

    plan = generate_meal_plan(age, gender, height, weight, goal, diet, activity, cuisine)

    ctx, _, _, maint, tgt, pro, fat, carb, *_ = build_user_context(age, gender, height, weight, goal, diet, activity, cuisine)
    
    bmi = calculate_bmi(weight, height)
    bmi_result = bmi_status(bmi)
    water = calculate_water_intake(weight)

    session['last_plan'] = plan

    return render_template(
        "result.html",
        plan=plan,
        bmi=bmi,
        bmi_result=bmi_result,
        calories=maint,
        target_calories=tgt,
        water=water,
        macros={'protein': pro, 'fat': fat, 'carbs': carb}
    )


@meal_bp.route("/generate-workout")
@login_required
def generate_workout():
    age, gender, height, weight, goal, diet, activity, cuisine = get_user_profile()

    workout_plan = generate_workout_plan(
        age, gender, height, weight, goal, activity
    )

    bmi = calculate_bmi(weight, height)
    bmi_result = bmi_status(bmi)

    return render_template(
        "workout_result.html",
        plan=workout_plan,
        bmi=bmi,
        bmi_result=bmi_result,
        goal=goal
    )





# --------- REPLACE SINGLE MEAL ---------

@meal_bp.route("/analyze-meal", methods=["POST"])
@login_required
def analyze_meal():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    try:
        image_bytes = file.read()
        from utils.ai import analyze_meal_image
        goal = current_user.goal or "Maintain Fitness"
        
        result = analyze_meal_image(image_bytes, goal)
        return jsonify(result)
    except Exception as e:
        print(f"[API] Error analyzing meal: {e}")
        return jsonify({"error": str(e)}), 500


@meal_bp.route("/replace-meal", methods=["POST"])
@login_required
def replace_meal():

    meal_type = request.json.get("meal_type")
    variation  = request.json.get("variation", 1)

    age, gender, height, weight, goal, diet, activity, cuisine = get_user_profile()

    new_meal = replace_single_meal(
        meal_type, age, gender, height, weight, goal, diet, activity, cuisine,
        variation=variation
    )

    return jsonify({"options": new_meal})


# --------- RESET ---------

@meal_bp.route("/reset-profile")
@login_required
def reset_profile():
    current_user.age = None
    current_user.gender = None
    current_user.height = None
    current_user.weight = None
    current_user.goal = None
    current_user.diet = None
    current_user.activity = None
    current_user.cuisine = None

    db.session.commit()
    return redirect(url_for("meal.dashboard"))

@meal_bp.route("/download-pdf")
@login_required
def download_pdf():

    plan = session.get('last_plan')

    if not plan:
        age, gender, height, weight, goal, diet, activity, cuisine = get_user_profile()
        plan = generate_meal_plan(age, gender, height, weight, goal, diet, activity, cuisine)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        rightMargin=72, leftMargin=72,
        topMargin=72, bottomMargin=72
    )
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("FitGenie — Your Daily Meal Plan", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    for meal_type, meal_text in plan.items():
        elements.append(Paragraph(meal_type, styles["Heading2"]))
        elements.append(Spacer(1, 0.15 * inch))

        items = [line.strip().strip("- ").strip() for line in meal_text.strip().split("\n") if line.strip()]
        bullet_points = [
            ListItem(Paragraph(item, styles["Normal"]))
            for item in items
        ]
        if bullet_points:
            elements.append(ListFlowable(bullet_points, bulletType='bullet'))
        elements.append(Spacer(1, 0.25 * inch))

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="FitGenie_Meal_Plan.pdf",
        mimetype="application/pdf"
    )