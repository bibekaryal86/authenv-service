# authenv-service

Converting https://github.com/bibekaryal86/authenticate-gateway-service to python
Deployed to: https://authenv-service.appspot.com/authenv-service/tests/ping in google-cloud-platform

# todo
* tests

# steps
* navigate to project's root
* setup virtual environment
  * python -m venv venv
* activate virtual environment
  * Windows (Powershell):
    * venv\Scripts\activate.ps1
  * Unix: 
    * source venv/Scripts/activate
* Install requirements
  * pip install .
  * OR, pip install -r requirements.txt -r requirements-dev.txt
  * Both options above install all dependencies, including optional for lint/test
  * In prod (gcp), pip install -r requirements.txt will suffice
* create/update config file
  * at project root:
    * cp .env.example .env
    * update .env with attribute values
* run main module
  * python src/authenv_service/main.py
* open swagger
  * http://localhost:8080/authenv-service/docs
* Setup linters
  * Install optional dependencies for lint
    * `pip install -r requirements-dev.txt`
    * `Flake8-pytest` is required because:
      * `flake8` doesn't support pyproject.toml
  * Run the lint commands (check only)
    * `isort src -c -v`
    * `isort tests -c -v`
    * `black src --check`
    * `black tests --check`
    * `flake8 src`
    * `flake8 tests`
  * To fix lint errors
    * `isort src`
    * `isort tests`
    * `black src`
    * `black tests`
* Setup tests
  * Install optional dependencies for tests
    * `pip install -r requirements-dev.txt`
  * Run tests
    * `pytest`

# notes
* when running from Pycharm:
  * script path: <PROJECT_ROOT>\src\authenv_service\main.py
  * working directory: <PROJECT_ROOT>

# google cloud platform
* gcp requires requirements.txt file for python applications
* hence moved dependencies from pyproject.toml to requirements.txt
