import json
import os
import re
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
gemini_api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

prompt = """You are an AI career coach. 
I will give you a list of technical skills that a user already has. 
Optionally, I may also provide a preferred learning path (like "Data Science", "Web Development", or "Cloud"). 

Your task:
- Suggest ONE most valuable next skill.
- Always return both the Learning Path and the Skill in JSON format.
- If the Learning Path is provided, keep it and only suggest the skill.
- If the Learning Path is empty, suggest both a suitable Learning Path and a Skill.
- If both User Skills and Learning Path are empty, suggest both a suitable Learning Path and a starting Skill.

Format your response strictly as JSON:
{
  "learning_path": "<learning_path>",
  "skill": "<skill>"
}

User skills: [Python, SQL]
Learning path: Data Science
"""
# response = model.generate_content(prompt)
# print(response.text.strip()) 
 
response = model.generate_content(prompt)

raw_output = response.text.strip()

# Remove Markdown code fences if they exist
cleaned = re.sub(r"^```(?:json)?|```$", "", raw_output, flags=re.MULTILINE).strip()

result = json.loads(cleaned)
print(result["learning_path"])
print(result["skill"])