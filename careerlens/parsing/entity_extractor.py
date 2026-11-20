import re
from datetime import datetime
def extract_profile(text):
 emails=re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",text);phones=re.findall(r"(?:\+?\d[\d ().-]{7,}\d)",text);years=[int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b",text)];current=datetime.now().year
 ranges=re.findall(r"\b(19\d{2}|20\d{2})\s*[-–]\s*(present|current|now|20\d{2})\b",text,re.I)
 experience=sum(max(0,min(current,current if end.lower() in ("present","current","now") else int(end))-int(start)) for start,end in ranges)
 degrees=[d for d in ("PhD","Master's","Bachelor's","B.Tech","M.Tech","MBA","B.Sc","M.Sc") if re.search(re.escape(d),text,re.I)]
 return {"email":emails[0] if emails else None,"phone":phones[0] if phones else None,"degrees":degrees,"estimated_experience":experience,"year_range":(min(years),max(years)) if years else None}
