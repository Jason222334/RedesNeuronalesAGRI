# GEMINI Project Context: Sistema Inteligente Agrícola - Valle Jequetepeque

This document provides essential context and instructions for the "Sistema Inteligente Agrícola" project, a full-stack application designed for managing agricultural data and predicting crop prices in the Valle Jequetepeque region.

## Project Overview

The project is a decision-support system for agriculture, featuring a web-based dashboard for data visualization and a machine learning component for price forecasting.

### Main Technologies

-   **Backend:** FastAPI (Python)
-   **Frontend:** React (TypeScript/JavaScript)
-   **Database:** PostgreSQL (hosted on Supabase) with SQLAlchemy ORM
-   **Machine Learning:** Scikit-learn (Random Forest Regressor), Pandas, Joblib/Pickle
-   **Data Visualization:** Recharts (Frontend)
-   **Reporting:** jsPDF, jspdf-autotable (Frontend)

### Architecture

The project follows a decoupled client-server architecture:
-   **`backend/`**: Contains the FastAPI application, database models, and ML logic.
    -   `routers/`: Modularized API endpoints (cultivos, reportes, auditoria).
    -   `ml_model/`: Contains the trained model (`modelo_entrenado.pkl`) and prediction logic (`predict.py`).
    -   `models_db.py`: Defines the SQLAlchemy database schema.
    -   `database.py`: Handles the database connection and session management.
-   **`frontend/`**: Contains the React application bootstrapped with Create React App.
    -   `src/pages/`: Main application views (Login, GestionCultivos).
    -   `src/components/`: Reusable UI components.
    -   `src/services/`: API communication layer (axios).

## Building and Running

### Backend (FastAPI)

1.  **Navigate to backend directory:** `cd backend`
2.  **Activate virtual environment:** `venv\Scripts\activate` (Windows)
3.  **Install dependencies:** `pip install -r requirements.txt`
4.  **Run the server:** `uvicorn main:app --reload`
    -   The API will be available at `http://localhost:8000`.
    -   Auto-generated documentation: `http://localhost:8000/docs`.

### Frontend (React)

1.  **Navigate to frontend directory:** `cd frontend`
2.  **Install dependencies:** `npm install`
3.  **Run the application:** `npm start`
    -   The application will be available at `http://localhost:3000`.

## Development Conventions

### Backend
-   **API Design:** Follow RESTful principles. Use Pydantic schemas for request and response validation.
-   **Database:** Use SQLAlchemy for all database interactions. Keep models synchronized with `models_db.py`.
-   - **Auditing:** All major actions (login, predictions) should be logged to the `bitacora_sucesos` table using the `registrar_bitacora` helper function.

### Frontend
-   **State Management:** Use React `useState` and `useEffect` for local state and side effects.
-   **Styling:** Primarily inline styles and standard CSS for the dashboard.
-   **API Calls:** Use `axios` for all backend communication, centralized in `services/api.js`.
-   **Reporting:** PDF generation is handled on the client-side using `jsPDF`.

## Key Files

-   `backend/main.py`: Entry point for the FastAPI application.
-   `backend/models_db.py`: Database schema definitions.
-   `backend/ml_model/predict.py`: Core machine learning prediction logic.
-   `frontend/src/App.js`: Main dashboard component with visualization and prediction interface.
-   `frontend/src/services/api.js`: Axios configuration for backend communication.

---
*Note: This file is intended for use by Gemini CLI to maintain project context.*
