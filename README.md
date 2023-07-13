# authenv-service

Converting https://github.com/bibekaryal86/authenticate-gateway-service to python


# todo
flake8
pytest
tox
black
logging
github actions flake8/black/pytest/tox
docker

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
  * pip install .
* create/update config file
  * at project root:
    * cp .env.example .env
    * update .env with attribute values
* run main module
  * python src/main.py
* open swagger
  * http://localhost:8080/authenv-service/docs
