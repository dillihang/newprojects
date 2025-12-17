FROM python:3.12-slim

WORKDIR /app

# Copy requirements
COPY Devopsandcloudautomation/devopsEx21/requirements.txt .

# Copy main script
COPY Devopsandcloudautomation/devopsEx15/githubapitolistrepos.py .

# Copy the dependency module (you need to find its location)
COPY Devopsandcloudautomation/devopsEx15/paginatedapifetcher.py .

RUN pip install -r requirements.txt


CMD ["python", "githubapitolistrepos.py"]