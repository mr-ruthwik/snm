# Simple Notes Management

Simple Notes Management is a secure, efficient web application built with Flask for organizing personal notes and managing files. Users can securely register, log in, create, update, delete notes, and upload/download files.

## Features

*   **User Authentication**: Secure registration and login, with OTP-based verification for new accounts.
*   **Notes Management**: Full CRUD (Create, Read, Update, Delete) functionality for personal notes.
*   **File Management**: Secure upload, storage, and retrieval of various file types.
*   **Data Export**: Capability to export all notes into an Excel file.
*   **Search**: Unified search function to quickly locate notes and files by keyword.
*   **Responsive UI**: Modern, clean user interface styled with Tailwind CSS.

## Tech Stack

*   **Backend**: Python, Flask
*   **Database**: MySQL
*   **Frontend**: HTML5, Tailwind CSS
*   **Utilities**: `itsdangerous` (token generation), `flask-excel` (data export), `smtplib` (email notifications)
