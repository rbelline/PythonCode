# Start the local mysql server on local machine WSL2
sudo /etc/init.d/mysql start
# stop the server
sudo /etc/init.d/mysql stop
# access mysql using the user
mysql -u {username} -p
# Detailed guide
# https://blog.rajnath.dev/mysql/#:~:text=You%20can%20install%20by%20follwoing%20instruction%20on%20WSL,default%20option%20or%20change%20based%20on%20your%20need.
# init dbt project
dbt init {project_name}
# check dbt version
dbt --version
# check connection
dbt debug
# edit profiles
nano ~/.dbt/profiles.yml
# use env variables
password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
export SNOWFLAKE_PASSWORD='your_password'
# test dbt
dbt test
# run dbt model
dbt run