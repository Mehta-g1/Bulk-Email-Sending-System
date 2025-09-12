# Bulk Email Sender

This is a Django-based web application for sending bulk emails. Users can sign up, manage their recipient lists, and send emails to multiple recipients at once. This project is designed to be a simple and effective tool for small-scale email campaigns.

## Project Status

**Under Development:** This project is currently under active development. New features are being added, and existing ones are being improved. Contributions are welcome!

## Features

*   **User Authentication:** Secure user sign-up and login system.
*   **Recipient Management:** Users can add, view, and manage their email recipients.
*   **Bulk Emailing:** Send emails to all registered recipients with a single click.
*   **SMTP Integration:** Uses SMTP to send emails, configured for Gmail by default but can be adapted for other providers.

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

4.  **Navigate to the project directory:**
    ```sh
    cd Email
    ```

5.  **Apply database migrations:**
    ```sh
    python manage.py migrate
    ```

6.  **Run the development server:**
    ```sh
    python manage.py runserver
    ```

The application will be available at `http://127.0.0.1:8000/`.

## How to Use

1.  **Sign Up:** Create a new account with your name, email address, and a password for the application. You will also need to provide the app password for your email account to be used for sending emails.
2.  **Login:** Log in with your credentials.
3.  **Dashboard:** After logging in, you will be redirected to your dashboard, where you can see your list of recipients.
4.  **Add Recipients:** (Functionality to add recipients to be implemented)
5.  **Send Emails:** Click the "Send Mail" button to send a test email to all your recipients.

## Contributing

Pull requests are welcome! This project is open for contributions. If you have suggestions for improvements or want to add new features, please feel free to open an issue or submit a pull request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m '''Add some AmazingFeature'''`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## Developer Credits

This project is maintained by:

*   **Vikash Kuamr Mehta** - *Initial Work*

We are grateful to all contributors who have helped and will help to improve this project.

## License

This project is licensed under the MIT License.
