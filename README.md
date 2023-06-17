# authenv-service

Converting https://github.com/bibekaryal86/authenticate-gateway-service to python


http://localhost:8080/authenv-service/docs
flake8
pytest
tox
black
logging

# steps
* navigate to project's root
* setup virtual environment
  * python -m venv venv
* activate virtual environment
  * Windows (Powershell):
    * venv\Scripts\activate.ps1
  * Unix: 
    * venv/Scripts/activate
* Install requirements
  * pip install -e .
* Set required environment variables
  * Windows (Powershell):
    * $Env:APP_ENV='some-app-env'
    * $Env:SECRET_KEY='some-secret-key'
    * $Env:MONGODB_USR_NAME='some-user-name'
    * $Env:MONGODB_USR_PWD='some-user-password'
    * $Env:BASIC_AUTH_USR='some-auth-user'
    * $Env:BASIC_AUTH_PWD='some-auth-password'
  * Unix:
    * export APP_ENV=some-app-env
    * export SECRET_KEY=some-secret-key
    * export MONGODB_USR_NAME=some-user-name
    * export MONGODB_USR_PWD = some-user-password
    * export BASIC_AUTH_USR=some-auth-user
    * export BASIC_AUTH_PWD = some-auth-password
* run main module
  * python src/main.py
