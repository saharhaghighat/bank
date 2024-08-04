# Bank Project

## Overview

The Bank project is a Django application designed to process transactions and generate reports. It is Dockerized for seamless development and deployment. The project uses Celery for periodic tasks and includes Postman collections for API testing.

## Project Structure

- bank/: Project root directory.
- transaction/: Django app for handling transactions.
- Postman API/: Directory containing Postman collections for API testing.

## Setup Instructions

### Prerequisites

Ensure you have Docker and Docker Compose installed on your machine.

### Clone the Repository

1. Clone the repository.
2. Navigate to the project directory.

### Build and Run Containers
```sh
docker-compose up --build
   ```

### Running Celery

- **Run Celery Worker**:
   ```sh
   docker-compose run --rm worker
   ```

  
- **Run Celery Beat**:
  ```sh
  docker-compose run --rm beat
  ```
  
### Management Commands

#### Update Transaction Summary
To update the transaction summary collection, use the following management command:
 ```sh
 python manage.py update_transaction_summary --mode <daily|weekly|monthly> --type <count|amount> --merchant-id <merchant-id>
   ```


**Parameters:**

- --mode: Specify the mode of the report (daily, weekly, or monthly).
- --type: Specify the type of report (count or amount).
- --merchant-id: Filter transactions by the merchant ID (optional).

**Example Command:**
```sh
 python manage.py update_transaction_summary --mode daily --type amount
   ```


#### Set Up Periodic Tasks
To configure periodic tasks for sending daily reports, run:
```sh
 python manage.py setup_periodic_tasks
   ```
This command will set up a periodic task to automatically send daily transaction reports.


## Docker

The project is Dockerized with configuration files.

### Running the Project with Docker

- **Build and Start Containers**:
  ```sh
  docker-compose up --build
   ```

  
- **Run Celery Worker and Beat**:
 ```sh
   docker-compose run --rm worker
   docker-compose run --rm beat
   ```

## Postman Collection

The Postman API folder contains collections for testing the APIs.

**Postman Collection Location:**

- **Directory**: Postman API
- **Format**: JSON files, ready to be imported into Postman.

