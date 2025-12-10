FROM python:3.13-slim

WORKDIR /app

COPY test_script.py .

HEALTHCHECK --interval=5s --timeout=3s --retries=3 CMD [ "python", "test_script.py"]

CMD ["sleep", "300"]