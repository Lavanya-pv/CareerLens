from careerlens.config import SCORE_WEIGHTS
def score_analysis(gaps,keyword_score,profile,section_count,semantic_score=.5):
 required=[g for g in gaps if g["required"]];skills=sum(1. if g["status"]=="matched" else .5 if g["status"]=="partial" else 0. for g in required)/max(1,len(required));completeness=min(1,section_count/4);experience=min(1,profile.get("estimated_experience",0)/5) if profile.get("estimated_experience") else .5
 parts={"skills":skills*100,"keywords":keyword_score*100,"experience":experience*100,"completeness":completeness*100,"semantic":max(0.,min(1.,semantic_score))*100}
 return round(sum(parts[k]*v for k,v in SCORE_WEIGHTS.items())),{k:round(v) for k,v in parts.items()}
