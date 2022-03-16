FROM python:3.10.2-slim
COPY . /src
WORKDIR /src
RUN pip3 install -r requirements.txt
CMD ["python3", "github_stars.py", "--help"]
