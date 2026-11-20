import json
from careerlens.db.database import connect
def save_analysis(filename,text,target_name,target_type,jd,score,breakdown,profile,recommendations,skills):
 with connect() as c:
  # Keep the legacy repository privacy-safe too: store neither resume contents,
  # identifying filenames, nor extracted contact details in analysis history.
  safe_profile={key:profile.get(key) for key in ("estimated_experience","degrees") if key in profile}
  rid=c.execute("INSERT INTO resumes(filename,raw_text) VALUES(?,?)",("Resume (private)","")).lastrowid;tid=c.execute("INSERT INTO targets(type,name,jd_text) VALUES(?,?,?)",(target_type,target_name,jd)).lastrowid
  aid=c.execute("INSERT INTO analyses(resume_id,target_id,overall_score,score_breakdown_json,profile_json,recommendations_json) VALUES(?,?,?,?,?,?)",(rid,tid,score,json.dumps(breakdown),json.dumps(safe_profile),json.dumps(recommendations))).lastrowid
  c.executemany("INSERT INTO analysis_skills(analysis_id,skill,status,confidence,category,required) VALUES(?,?,?,?,?,?)",[(aid,s["name"],s["status"],s["confidence"],s["category"],int(s["required"])) for s in skills])
 return aid
def get_recent_analyses(limit=25):
 with connect() as c:
  rows=c.execute("SELECT a.*,r.filename,t.name target_name,(SELECT COUNT(*) FROM analysis_skills s WHERE s.analysis_id=a.id AND s.status='missing') missing_count FROM analyses a JOIN resumes r ON r.id=a.resume_id JOIN targets t ON t.id=a.target_id ORDER BY a.created_at DESC,a.id DESC LIMIT ?",(limit,)).fetchall();return [dict(r) for r in rows]
def get_analysis(aid):
 with connect() as c:
  row=c.execute("SELECT a.*,r.filename,r.raw_text,t.name target_name,t.jd_text FROM analyses a JOIN resumes r ON r.id=a.resume_id JOIN targets t ON t.id=a.target_id WHERE a.id=?",(aid,)).fetchone()
  if not row:return None
  result=dict(row);result["breakdown"]=json.loads(result.pop("score_breakdown_json"));result["profile"]=json.loads(result.pop("profile_json"));result["recommendations"]=json.loads(result.pop("recommendations_json"));result["skills"]=[dict(s) for s in c.execute("SELECT * FROM analysis_skills WHERE analysis_id=?",(aid,))];return result
