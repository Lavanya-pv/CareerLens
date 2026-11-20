import csv
from careerlens.config import DATA_DIR
def get_learning_plan(missing):
 """Read the shared, editable CSV resource catalog (no duplicate JSON catalog)."""
 with (DATA_DIR/"learning_resources.csv").open(encoding="utf-8-sig",newline="") as f:
  resources={row["skill"].casefold():row for row in csv.DictReader(f)}
 return [
  {"skill":skill,"resource":resources[skill.casefold()]["resource_name"],"project":resources[skill.casefold()]["project_idea"]}
  for skill in missing if skill.casefold() in resources
 ]
