import re
import json
from flask import Flask, request, jsonify, render_template
from utils.db import get_connection
import google.generativeai as genai
import os
from dotenv import load_dotenv

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("index.html")


@app.route("/user", methods=["POST"])
def add_user():
    data = request.json
    name = data["name"]
    skills = data.get("skills", [])        # Keep as Python list
    learning_path = data.get("learning_path", "")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Insert into PostgreSQL, return the generated id
        cursor.execute(
            "INSERT INTO users (name, skills, learning_path) VALUES (%s, %s, %s) RETURNING id;",
            (name, skills, learning_path)
        )
        user_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({"message": "User added successfully", "user_id": user_id}), 201

    finally:
        cursor.close()
        conn.close()


@app.route("/recommend/<int:user_id>", methods=["GET"])
def recommend(user_id):
    load_dotenv()
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel("gemini-2.5-flash-lite")

    # Fetch user data
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, skills, learning_path FROM users WHERE id=%s;", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id, name, user_skills, learning_path = user
    user_skills = user_skills or []

    prompt = f"""
    You are an AI career coach.
    I will give you a list of technical skills that a user already has.
    Optionally, I may also provide a preferred learning path (like "Data Science", "Web Development", or "Cloud").

    Your task:
    - Suggest ONE most valuable next skill.
    - Always return both the Learning Path and the Skill in JSON format.
    - If the Learning Path is provided, keep it and only suggest the skill.
    - If the Learning Path is empty, suggest both a suitable Learning Path and a Skill.
    - If both User Skills and Learning Path are empty, suggest both a suitable Learning Path and a starting Skill.

    Format strictly as JSON:
    {{
        "learning_path": "<learning_path>",
        "recommendation": "<skill>"
    }}

    User skills: {user_skills}
    Learning path: {learning_path}
    """

    response = model.generate_content(prompt)
    raw_output = response.text.strip()
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw_output, flags=re.MULTILINE).strip()
    result = json.loads(cleaned)

    return jsonify({
        "id": [user_id],
        "name": [name],
        "learning_path": result["learning_path"],
        "next-skill": result["recommendation"],
        "skills": [user_skills]
    })


@app.route("/skills/<int:user_id>", methods=["GET"])
def skills(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, skills, learning_path FROM users WHERE id=%s;", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id, name, user_skills, learning_path = user
    user_skills = user_skills or []

    return jsonify({
        "id": [user_id],
        "name": [name],
        "learning_path": [learning_path],
        "skills": [user_skills]
    })


@app.route("/add_skills/<int:user_id>", methods=["POST"])
def add_skills(user_id):
    data = request.json
    new_skill = data.get("skills")           # Always a string
    learning_path = data.get("learning_path")  # Optional

    if not new_skill:
        return jsonify({"error": "No skill provided"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Fetch current skills
        cursor.execute("SELECT skills FROM users WHERE id=%s;", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        current_skills = user[0] or []

        # Avoid duplicates
        if new_skill not in current_skills:
            current_skills.append(new_skill)

        # Update DB
        cursor.execute(
            "UPDATE users SET skills=%s, learning_path=%s WHERE id=%s;",
            (current_skills, learning_path, user_id)
        )
        conn.commit()

        return jsonify({
            "message": "Skill added successfully",
            "user_id": user_id,
            "skills": current_skills,
            "learning_path": learning_path
        }), 200

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    app.run(debug=True)
