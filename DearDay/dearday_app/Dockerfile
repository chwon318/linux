FROM python:3.11.6

WORKDIR /usr/src/app

COPY requirements.txt .
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

COPY . .
RUN sed -i 's/\r$//' /usr/src/app/entrypoint.sh && chmod +x /usr/src/app/entrypoint.sh

CMD ["sh", "/usr/src/app/entrypoint.sh"]
EXPOSE 8000
