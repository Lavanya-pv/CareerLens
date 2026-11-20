def keyword_coverage(jd,resume):
 try:
  from sklearn.feature_extraction.text import TfidfVectorizer
  v=TfidfVectorizer(stop_words="english",ngram_range=(1,2),max_features=24);m=v.fit_transform([jd]);terms=v.get_feature_names_out();weights=m.toarray()[0];keywords=[w for w,_ in sorted(zip(terms,weights),key=lambda x:x[1],reverse=True)[:16]]
 except (ImportError,ValueError): keywords=list(dict.fromkeys(w.lower() for w in jd.split() if len(w)>4))[:16]
 present=[w for w in keywords if w.lower() in resume.lower()]
 return (len(present)/len(keywords) if keywords else .5),keywords
