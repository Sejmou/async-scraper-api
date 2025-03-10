# Distributed Scraping Infrastructure
This project is my attempt at coming up with my own scraper infrastructure that can scale across several machines, hosted anywhere in the internet. My vision is creating a network of scrapers that can be controlled and monitored from a central admin dashboard.

## Components
- Scraper API Server (`./api-server`): A RESTful API server written in Python that should be deployed across several machines. Each instance can run scraper jobs independently. Each job first writes data to a local JSONL file which is eventually uploaded to specific prefixes in the specified S3 bucket (in compressed format).
- API docs (`./api-docs`): A [Bruno](https://www.usebruno.com/) collection of example requests for the API server.
- Local S3 instance (`./local-s3`): A local MinIO S3 instance that can be used for testing purposes and launched via Docker Compose. 
- Admin Dashboard (`./admin-dashboard`): A web application that can be used to control and monitor the scraper instances. It should be able to start/stop jobs and show details about the status of each job.