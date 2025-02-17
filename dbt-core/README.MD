# Create dbt virtual environemnt
python3 -m venv dbt-env
# Activate virtual environemnt
source dbt-env/bin/activate
# Install dbt core
pip install dbt-core
# Check dbt version
dbt --version
# init a project
dbt init project_name
