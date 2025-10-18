# Users Microservice 

## Overview
Demonstrates the design and documentation of RESTful microservices using both **code-first** and **API-first** approaches.  
The Users microservice contains three primary resources:

- **Profiles** – user profile information  
- **Photos** – photos associated with each profile  
- **Visibility** – profile visibility and availability settings  

---

## Microservice Design Summary

### 1. Profiles
Defines CRUD endpoints for `/profiles`, including:
- `GET /profiles` – list all profiles  
- `GET /profiles/{profile_id}` – retrieve a single profile  
- `POST /profiles` – create a new profile  
- `PUT /profiles/{profile_id}` – update a profile  
- `DELETE /profiles/{profile_id}` – delete a profile  

---

### 2. Photos 
Defines CRUD endpoints for `/photos`, including:
- `GET /photos` – list all photos  
- `GET /photos/{photo_id}` – retrieve a single photo  
- `POST /photos` – upload a new photo  
- `PUT /photos/{photo_id}` – update a photo  
- `DELETE /photos/{photo_id}` – delete a photo  

---

### 3. Visibility  
Defines CRUD endpoints for /visibility, which manage whether user profiles are visible, their visibility scope (e.g., close, normal, wide), and timestamps for when visibility was last toggled.
Endpoints:
- `GET /visibility` – list all visibility records
- `GET /visibility/{visibility_id}` – retrieve a single visibility record
- `POST /visibility` – create a new visibility record
- `PUT /visibility/{visibility_id}` – update visibility status or scope
- `DELETE /visibility/{visibility_id}` – delete a visibility record

For this microservice, I used Swagger to do API 1st definition of the microservice’s API.
You can open the yaml file in [Swagger Editor](https://editor.swagger.io) to view, test, and validate the API definition interactively.

---

## ⚙️ How to View & Test

### View FastAPI Docs
Run the code-first services:

uvicorn main:app --reload
Then visit:
http://127.0.0.1:8000/docs → Swagger UI
http://127.0.0.1:8000/health → Health check

Test the API-First Definition
Open Swagger Editor
Select File → Import File
Load visibility_api.yaml
View the interactive documentation and use Try It Out to simulate requests.