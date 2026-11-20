def rank_roles(resume_skills,roles):
 results=[]
 for role in roles:
  req=set(role.get("required",[]));pref=set(role.get("preferred",[]));score=.75*len(req&resume_skills)/max(1,len(req))+.25*len(pref&resume_skills)/max(1,len(pref))
  results.append({"name":role["name"],"score":score,"matched":sorted((req|pref)&resume_skills),"missing":sorted((req|pref)-resume_skills)})
 return sorted(results,key=lambda x:x["score"],reverse=True)
