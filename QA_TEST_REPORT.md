# CareerLens AI QA Integration Report

**Result:** 12 of 12 requested scenarios passed their behavioral assertions against the implemented modules. Tests generated real PDFs in memory and used the actual analysis service, recommender, and SQLite database with isolated temporary files. They did not substitute mock scores or fake successful analysis responses.

**How to rerun:**

```powershell
.\venv\Scripts\python.exe -m unittest tests.test_qa_scenarios -v
```

## Priority findings

| Priority | Finding | Impact | Required action |
|---|---|---|---|
| **P1** | The local Sentence Transformers model is not present in this environment. The actual semantic matcher reported `tfidf-fallback`. | Similarity reflects word overlap rather than embedding-based meaning. Paraphrases may receive low scores and can be classified missing instead of partial. | Download/cache `sentence-transformers/all-MiniLM-L6-v2` locally, then rerun semantic and gap tests. No hosted API is used. |
| **P3** | `XGBoost` is in the skill taxonomy but has no curated learning resource row. | The gap remains visible, but its recommendation has no URL or project resource. | Add a vetted free resource row to `data/learning_resources.csv` if one is selected. The engine handles this case without attaching an unrelated resource. |

No P0 blocker was found in the tested UI service path. Empty and invalid inputs fail with readable validation errors; analysis outputs are saved and retrieved; repeated runs create separate history records.

## Scenario results

### 1. Valid resume and complete job description — PASS

- **Expected:** Parse the PDF, find overlapping skills, compute bounded component and overall scores, produce gaps/recommendations, and save history.
- **Actual:** Analysis returned a saved ID, direct skill matches, and all three component scores (`required_skill_coverage`, `semantic_relevance`, `experience_qualifications`); overall score was within 0–100.
- **Possible failure point:** Missing local MiniLM makes the semantic component use TF-IDF (P1 above).
- **Required fix:** None for integration. Cache MiniLM for true embedding-based comparisons.

### 2. Resume with no technical skills — PASS

- **Expected:** Do not invent resume skills; classify recognizable JD skills as missing and recommend matching learning resources.
- **Actual:** No direct matches; Python, SQL, and Docker appeared as missing, and the recommendation engine returned those same skills.
- **Possible failure point:** A resume phrase that coincidentally matches a dictionary alias can be extracted as a skill.
- **Required fix:** None observed. Review taxonomy aliases if a false positive is reported.

### 3. Empty job description — PASS

- **Expected:** Reject before analysis or persistence with a clear prompt.
- **Actual:** `ValueError` indicating a job description is required; no analysis was saved.
- **Possible failure point:** UI and service validation messages could drift.
- **Required fix:** None; the service currently enforces this contract.

### 4. Invalid or corrupted PDF — PASS

- **Expected:** Return a readable PDF error and avoid saving a completed analysis.
- **Actual:** Invalid bytes raised the parser’s `PDFReadError` (“could not read”); Streamlit catches the error and displays it.
- **Possible failure point:** A structurally valid but unusual PDF may fail in the underlying parser.
- **Required fix:** None observed. Keep the parser’s error boundary and user-facing message.

### 5. Resume containing duplicate skills — PASS

- **Expected:** Return one canonical entry per skill despite repeated spellings/case.
- **Actual:** Repeated `Python` and `SQL` tokens produced one extracted skill each.
- **Possible failure point:** Duplicate aliases in the skills CSV could map distinct canonical skills from the same token.
- **Required fix:** None observed; continue validating taxonomy alias collisions when editing the CSV.

### 6. Job description containing an uncommon technical skill — PASS

- **Expected:** Recognize supported uncommon skills and compare them normally.
- **Actual:** `XGBoost` was extracted from the JD and directly matched the resume.
- **Possible failure point:** Skills absent from the curated CSV cannot be found by taxonomy matching; TF-IDF does not add canonical skills to the taxonomy.
- **Required fix:** Add new canonical skills and aliases to `data/skills_database.csv`. Add resources separately when available.

### 7. Abbreviations and synonyms — PASS

- **Expected:** Normalize resume `ML`, `NLP`, and `JS` to canonical JD terms.
- **Actual:** They directly matched `Machine Learning`, `Natural Language Processing`, and `JavaScript`.
- **Possible failure point:** A missing alias in the CSV prevents direct normalization; semantic fallback may not reliably repair it.
- **Required fix:** None for these aliases. Add future variants to the CSV.

### 8. Very short resume — PASS

- **Expected:** Analyze a short text PDF without inventing content and warn that extracted text is sparse.
- **Actual:** `Python` matched; the parser returned its low-text warning, and analysis completed.
- **Possible failure point:** Extremely sparse evidence can still produce a compatibility score that users may overinterpret.
- **Required fix:** None observed. Preserve the warning and indicative-score disclaimer in the UI/report.

### 9. Very long resume — PASS

- **Expected:** Extract text from every page and complete analysis without truncating the tested content.
- **Actual:** A generated multi-page resume exceeded 20,000 extracted characters, parsed across pages, and produced matched skills.
- **Possible failure point:** No explicit upload/page/text-size limit was observed; exceptionally large PDFs can consume memory or increase latency.
- **Required fix:** Not required for the tested size. Consider a documented file/page limit if larger uploads are expected.

### 10. Missing learning resource — PASS

- **Expected:** Keep the skill gap, avoid unrelated courses, and clearly indicate that no curated resource exists.
- **Actual:** XGBoost returned a recommendation entry with no URL and a “No curated resource” explanation; no unrelated resource was attached.
- **Possible failure point:** The user has no direct learning link for this skill.
- **Required fix:** Optional data improvement: add a verified resource row for XGBoost.

### 11. Empty analysis history — PASS

- **Expected:** Return an empty list and let the UI show its empty-state message.
- **Actual:** A newly initialized temporary SQLite database returned `[]` without error.
- **Possible failure point:** A damaged or inaccessible database file raises a database error.
- **Required fix:** None observed; the history page already handles an empty result.

### 12. Repeated analysis of the same resume — PASS

- **Expected:** Re-run analysis and persist each completed run so history tracks analyses over time.
- **Actual:** Two actual service calls produced distinct analysis IDs and two history entries with the same score.
- **Possible failure point:** Repeated runs are not deduplicated and will increase history count.
- **Required fix:** None for current history behavior. Add deduplication only if product requirements change.

## Test implementation

The executable scenarios are in [tests/test_qa_scenarios.py](tests/test_qa_scenarios.py). Each test uses real module calls, generated PDF bytes, and a temporary SQLite database; the missing-resource case reads the project’s actual CSV catalog.
