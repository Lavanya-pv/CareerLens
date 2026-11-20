def get_resume_tips(text,sections):
 tips=[]
 if "Experience" not in sections:tips.append("Add an Experience section with role, employer, dates, and impact.")
 if "Projects" not in sections:tips.append("Add 2–3 projects that demonstrate skills this role asks for.")
 if not any(char.isdigit() for char in text):tips.append("Add measurable outcomes to a few bullets, such as time saved or users supported.")
 words=len(text.split())
 if words<180:tips.append("Your resume is brief; add relevant accomplishments and context.")
 elif words>1100:tips.append("Consider trimming older or less relevant details to keep the resume focused.")
 return tips or ["Your resume has a solid structure. Lead with accomplishments most relevant to your target role."]
