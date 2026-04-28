FROM python:3.11.6

WORKDIR /usr/src/app

COPY requirements.txt .
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

COPY . .

CMD ["./entrypoint.sh"]
EXPOSE 8000
