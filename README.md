# Bulk Email Sender

This is a Django-based web application for sending bulk emails. Users can sign up, manage their recipient lists, and send emails to multiple recipients at once. This project is designed to be a simple and effective tool for small-scale email campaigns.

## Project Status

**Under Development:** This project is currently under active development. New features are being added, and existing ones are being improved. Contributions are welcome!

## Project Structure

The project is organized into the following Django apps:

*   `CreateUser`: Handles user authentication, registration, profile management, and password reset functionality.
*   `Home`: Manages the static pages of the website like the homepage, about, and contact pages.
*   `Receipent`: This functionality is handled through the `CreateUser` app, with templates in the `Receipent` directory, allowing users to manage their email recipients.

## Features

*   **User Authentication:** Secure user sign-up, login, and logout system.
*   **Profile Management:** Users can view and edit their profiles, including personal information and profile picture.
*   **Password Reset:** Secure password reset functionality using email verification.
*   **Recipient Management:** Users can add, view, edit, and delete their email recipients.
*   **Bulk Recipient Upload:** Add recipients in bulk using file uploads.
*   **Bulk Emailing:** Send emails to all registered recipients with a single click.
*   **SMTP Integration:** Uses SMTP to send emails, configured via environment variables.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

*   Python 3.10 or higher
*   Pip (Python package installer)

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/Mehta-g1/Bulk-Email-Sending-System.git
    cd Bulk-Email-Sending-System
    ```

2.  **Create a virtual environment (recommended):**
    ```sh
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the `Email` directory and add your email credentials:
    ```
    EMAIL_HOST_USER=your-email@gmail.com
    EMAIL_HOST_PASSWORD=your-app-password
    ```

5.  **Navigate to the project directory:**
    ```sh
    cd Email
    ```

6.  **Apply database migrations:**
    ```sh
    python manage.py migrate
    ```

7.  **Run the development server:**
    ```sh
    python manage.py runserver
    ```

The application will be available at `http://127.0.0.1:8000/`.

## Future Improvements

*   **Email Scheduling:** Implement a feature to schedule emails to be sent at a specific date and time.
*   **Email Templates:** Allow users to create and save email templates for reuse.
*   **Analytics and Reporting:** Track email open rates, click-through rates, and other engagement metrics.
*   **Celery Integration:** Use Celery for asynchronous task processing to handle sending large volumes of emails without blocking the main application.
*   **Advanced User Roles:** Introduce different user roles and permissions (e.g., admin, user).
*   **API Endpoints:** Develop a RESTful API to allow other applications to interact with the email sending service.
*   **Enhanced Security:** Implement two-factor authentication (2FA) for user accounts.

## Contributing

Pull requests are welcome! This project is open for contributions. If you have suggestions for improvements or want to add new features, please feel free to open an issue or submit a pull request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## Developer Credits

This project is maintained by:

*   **Vikash Kuamr Mehta** - *Initial Work*

We are grateful to all contributors who have helped and will help to improve this project.

## License

This project is licensed under the MIT License.