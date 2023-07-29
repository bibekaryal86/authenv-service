# authenv-service

Converting https://github.com/bibekaryal86/authenticate-gateway-service to python


# todo
* flake8
* pytest
* tox
* black
* github actions flake8/black/pytest/tox
* logging

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
* create/update config file
  * at project root:
    * cp .env.example .env
    * update .env with attribute values
* run main module
  * python src/main.py
* open swagger
  * http://localhost:8080/authenv-service/docs
* Setup linters
  * First install optional dependencies
    * `pip install '.[lint]' .`
    * `Flake8-pytest` is required because:
      * `flake8` doesn't support pyproject.toml
      * I don't want to maintain another config file
  * Run the lint commands (check only)
    * `isort src -c -v`
    * `isort test -c -v`
    * `black src --check`
    * `black test --check`
    * `flake8 src`
    * `flake8 test`
  * To fix lint errors
    * `isort src`
    * `isort test`
    * `black src`
    * `black test`

# notes
* when running from Pycharm:
  * script path: <PROJECT_ROOT>\src\authenv_service\main.py
  * working directory: <PROJECT_ROOT>
