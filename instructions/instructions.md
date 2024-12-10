# Product Requirement Document (PRD) for Dynamic Form Engine Backend

## Project Overview

The project aims to develop the backend for a dynamic form engine that manages form templates in JSON format. The backend will provide an admin dashboard for managing forms and two API endpoints for retrieving form data. SQLite will be used as the database, and the project will be built using Python with Flask.

## Functional Requirements

### 1. Admin Dashboard

The admin dashboard will allow admins to manage form templates via a web interface built with HTML/CSS. The functionalities include:

#### a. View Existing Form Templates

- A list view displaying existing form templates
- Each row in the list will show:
  - Form ID
  - Form Name
  - Uploaded Date

#### b. Add New Form Template

- A button to add a new form template
- On clicking the button:
  - Admin will see input fields to:
    - Enter the form name
    - Upload a JSON file containing the form template
- On submission:
  - The JSON file will be stored in the `uploaded_json_structure` directory with a UUID filename corresponding to the form ID
  - The following data will be saved in the SQLite `forms` table:
    - Form ID (UUID)
    - Form Name
    - Uploaded Date
    - File Path (relative path of the JSON file)

#### c. Form Listing

- Newly added forms should immediately appear in the list of form templates

### 2. API Endpoints

#### a. Retrieve List of Form Templates

- **Endpoint:** `/api/forms`
- **Method:** GET
- **Response:** JSON array containing:
  - Form ID
  - Form Name

**Example Response:**

```json
[
  {
    "formId": "unique_form_id_1",
    "formName": "Sample Form 1"
  },
  {
    "formId": "unique_form_id_2",
    "formName": "Sample Form 2"
  }
]
```

#### b. Retrieve Form Template by ID

- **Endpoint:** `/api/forms/<formId>`
- **Method:** GET
- **Parameters:**
  - `formId`: The unique ID of the form
- **Response:** The JSON structure of the form template (previously uploaded)

**Example Response:**

```json
{
  "formId": "unique_form_id",
  "formName": "Dynamic Form Sample",
  "pages": [
    {
      "title": "Page Title",
      "fields": []
    }
  ]
}
```

## Technical Requirements

### 1. Directory Structure

- A directory named `uploaded_json_structure` to store uploaded JSON files
- Each file will be named using a UUID matching the form ID

### 2. Database Schema

- **Database:** SQLite
- **Table:** forms
- **Columns:**
  - `formId` (TEXT, Primary Key): UUID of the form
  - `formName` (TEXT): Name of the form
  - `uploadedDate` (TEXT): Date and time when the form was uploaded
  - `formPath` (TEXT): Path to the JSON file in the `uploaded_json_structure` directory

### 3. Flask App Structure

**Routes:**

- `/admin` (GET/POST): Serves the admin dashboard interface
- `/api/forms` (GET): Fetches the list of form templates
- `/api/forms/<formId>` (GET): Fetches the JSON structure of a form by ID

## Non-Functional Requirements

- **Scalability:** The system should be capable of managing a large number of form templates
- **Performance:** APIs should respond within 500ms for typical requests
- **Error Handling:** Provide meaningful error messages for invalid inputs, missing files, or database issues
- **Maintainability:** The code should follow best practices for readability and reusability

## Steps to Build the System

### Step 1: Setup Flask Project

- Initialize a Flask application
- Configure the SQLite database

### Step 2: Implement Admin Dashboard

- Build the HTML/CSS interface for the admin dashboard
- Add features to:
  - Display a list of forms
  - Provide a form for uploading JSON files and adding form templates

### Step 3: Setup Directory for JSON Storage

- Create the `uploaded_json_structure` directory
- Ensure uploaded JSON files are stored with UUID filenames

### Step 4: Implement API Endpoints

- Add `/api/forms` endpoint to fetch the list of forms
- Add `/api/forms/<formId>` endpoint to fetch a form's JSON data

### Step 5: Database Integration

- Design and create the forms table in SQLite
- Implement logic to:
  - Insert new form records when a template is added
  - Query form data for API endpoints

## Deliverables

- Flask application with admin dashboard and APIs
- SQLite database with the forms table
- Directory structure for storing JSON files
- Complete HTML/CSS files for the admin dashboard interface
- Comprehensive documentation on the project structure and API usage
