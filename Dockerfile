FROM python:3.13.0-alpine
WORKDIR /code
COPY ./src /code/src
COPY .env /code
COPY pyproject.toml /code
RUN pip install --no-cache-dir --upgrade .
# instead of `.` use -r requirements.txt if using such
ENV APP_PORT=8080
# CMD ["uvicorn", "src.authenv_service.main:app", "--host", "0.0.0.0", "--port", "80"]
ENTRYPOINT ["python", "src/authenv_service/main.py"]
# build as : docker build -t authenv-service .
# run as : docker run --name authenv-service -e PYTHONUNBUFFERED=1 -p 8080:8080 -d authenv-service
# remove PYTHONBUFFERED env variable after adding logging (it is in README.md todos)
