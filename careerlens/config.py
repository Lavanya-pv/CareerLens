from pathlib import Path
BASE_DIR=Path(__file__).resolve().parent.parent
DATA_DIR=BASE_DIR/"data"
ROLE_PROFILES_PATH=DATA_DIR/"role_profiles.json"
DB_PATH=BASE_DIR/"database"/"careerlens.db"
MODEL_NAME="sentence-transformers/all-MiniLM-L6-v2"
SCORE_WEIGHTS={"skills":.4,"keywords":.2,"experience":.15,"completeness":.15,"semantic":.1}
