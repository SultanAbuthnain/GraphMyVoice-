# Audio-to-Mindmap Learning Assistant

Audio-to-Mindmap Learning Assistant is a comprehensive system designed to automatically convert recorded audio lectures into interactive, structured mind maps and actionable tasks.

This application is a collaborative capstone project developed by two students:
*   Frontend Developer: Responsible for the React/Next.js user interface and interactive mind map visualization.
*   Backend Developer: Responsible for the FastAPI architecture, database design, and the AI agent pipeline using LangGraph and Google Gemini.

## System Architecture

The application is split into two primary components:

1.  **Backend (`/backend`)**: A robust API built with FastAPI, SQLAlchemy, and LangGraph. It handles audio ingestion, transcription, and mind map extraction using Google Gemini 1.5. Data is persisted in a PostgreSQL database.
2.  **Frontend (`/frontend`)**: A modern web application built with Next.js and ReactFlow. It allows users to upload audio, view real-time processing status, interact with the generated mind map, and manage extracted tasks and notes.

## Technologies Used

### Backend Stack
*   **FastAPI**: A modern, high-performance web framework for building the RESTful API. Selected for its speed, asynchronous support, and automatic OpenAPI documentation.
*   **LangGraph**: A library for building stateful, multi-actor applications with Large Language Models. Used to orchestrate the complex AI pipeline consisting of transcription, pre-processing guardrails, extraction, and post-processing validation.
*   **Google Gemini 1.5**: The core AI engine powering the application. Utilized via the `google-genai` SDK for its massive context window and native audio processing capabilities to transcribe audio and intelligently extract structured mind map data.
*   **PostgreSQL & SQLAlchemy**: The primary relational database and Object Relational Mapper (ORM) utilized for robust data persistence, schema management, and ensuring relational integrity.
*   **Alembic**: Database migration tool used alongside SQLAlchemy to track and manage database schema changes over time.
*   **Pytest**: Used for building the asynchronous unit testing infrastructure to ensure API reliability.

### Frontend Stack
*   **Next.js & React**: The core framework utilized for building a responsive, modern user interface with optimized rendering and efficient routing.
*   **React Flow**: A highly customizable library utilized specifically for rendering the interactive, node-based mind map interface.
*   **Tailwind CSS**: A utility-first CSS framework employed for rapid UI development and maintaining a consistent, professional design system.

## Prerequisites

Ensure you have the following installed on your system before proceeding:
*   Python 3.10+
*   Node.js 18+
*   PostgreSQL 16+ (or Docker to run the database container)
*   A valid Google Gemini API Key

## Setup Guide

Follow the steps below to set up both the backend and frontend environments.

### 1. Backend Setup

Navigate to the backend directory:
```bash
cd backend
```

**Environment Variables**
Create a copy of the example environment file:
```bash
cp .env.example .env
```
Open the newly created `.env` file and insert your `GEMINI_API_KEY`. Modify the database URL if your local PostgreSQL instance uses different credentials.

**Install Dependencies**
Create a virtual environment and install the required Python packages:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

**Database Setup**
Ensure your PostgreSQL server is running and the database specified in your `.env` exists. Apply the database migrations:
```bash
alembic upgrade head
```

**Run the Backend Server**
Start the FastAPI server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The API documentation (Swagger UI) will be available at: http://localhost:8000/docs

### 2. Frontend Setup

Open a new terminal session and navigate to the frontend directory:
```bash
cd frontend
```

**Environment Variables**
Create the local environment file:
```bash
cp .env.example .env.local
```
Ensure `NEXT_PUBLIC_API_BASE` is set to `http://localhost:8000/api/v1`.

**Install Dependencies**
Install the necessary Node packages:
```bash
npm install
```

**Run the Frontend Server**
Start the Next.js development server:
```bash
npm run dev
```
The application will be accessible at: http://localhost:3000

## Running with Docker

For a streamlined deployment, you can run the backend and the database using Docker Compose.

1.  Navigate to the `backend` directory.
2.  Ensure your `backend/.env` file is properly configured with your Gemini API key.
3.  Run the following command:
```bash
docker-compose up --build -d
```
This command will provision the PostgreSQL database, run the Alembic migrations, and start the FastAPI backend service automatically.

## Testing

The backend includes a suite of unit tests. To run the tests, ensure you are in the `backend` directory with your virtual environment activated, then execute:

```bash
export PYTHONPATH="."  # On Windows PowerShell use: $env:PYTHONPATH="."
pytest
```
