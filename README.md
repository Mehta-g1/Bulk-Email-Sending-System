# Bulk Email Sending System

A powerful, user-friendly, and secure Django-based web application designed for sending bulk emails efficiently. This system allows multi-user support where each user can manage their own recipients, groups, templates, and SMTP configurations to run personalized email campaigns.

**Live Demo:** [https://emailsender.pythonanywhere.com/](https://emailsender.pythonanywhere.com/)

---

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Setup](#environment-setup)
- [User Guide](#user-guide)
  - [Authentication](#authentication)
  - [Dashboard & Analytics](#dashboard--analytics)
  - [Group Management](#group-management)
  - [Recipient Management (Bulk Upload Policy)](#recipient-management)
  - [Template System](#template-system)
  - [SMTP Configuration (BYOS)](#smtp-configuration-byos)
  - [Sending Emails](#sending-emails)
- [API & URL Map](#api--url-map)
- [Future Improvements](#future-improvements)
- [Contributing](#contributing)
- [License](#license)

---

## Features

*   **Secure Authentication**: Complete sign-up, login, password reset (via email link), and functionality to manage personal profiles.
*   **Custom SMTP Configuration (BYOS)**: "Bring Your Own Server" model. Each user configures their own SMTP credentials (Gmail, Outlook, Zoho, etc.) directly in their account settings, ensuring their campaigns use their own reputation and limits.
*   **Group Management**: Create, edit, and delete groups to organize recipients effectively (e.g., "Newsletter", "Clients", "Team").
*   **Smart Bulk Import**: Upload recipients via CSV or Excel (XLS/XLSX). The system intelligently maps columns (finding flexible matches like 'Name', 'Fullname', 'Email', 'E-mail') and ignores duplicates automatically.
*   **Template Engine**: Create rich HTML email templates. Set a "Primary" template for quick access.
*   **Dashboard Analytics**: Visual progress bars for profile completion, quick stats on groups, and recent activity logs.
*   **Bulk Emailing**: Select individual recipients or filter by group to send emails in bulk with a single click.
*   **Attachment Handling**: Manages uploaded files for bulk import with options to read/delete file history.

---

## Screenshots

| Feature | Description |
| :--- | :--- |
| **Home Page** | Landing page with project overview. |
| **Dashboard** | Central hub showing recipient stats and groups. |
| **Account Settings** | **Unique Feature:** Configure your personal SMTP (Gmail/Outlook) here. |
| **Group Manager** | specialized interface to create and manage recipient groups. |
| **Template Editor** | Create reusable email contents with subjects. |

*(See specific screenshots in the `screenshots/` directory)*

---

## Technology Stack

*   **Backend Framework**: Django 5.x (Python 3.10+)
*   **Database**: SQLite (Default) - Can be easily switched to PostgreSQL/MySQL via Django settings.
*   **Frontend**: HTML5, CSS3, Vanilla JavaScript (No heavy framework overhead).
*   **Data Processing**: Pandas (for robust CSV/Excel parsing).
*   **Configuration**: Python-Decouple (for environment variable management).
*   **Static Files**: Whitenoise (for serving static assets in production).

---

## Project Structure

```text
Email Send/
├── .env                  # Environment variables (created by you)
├── requirements.txt      # Python dependencies
├── README.md             # Documentation
├── Email/                # Main Project Directory
    ├── manage.py         # Django management script
    ├── Email/            # Project Settings
    │   ├── settings.py   # Main configuration
    │   ├── urls.py       # Global URL routing
    │   └── wsgi.py       # WSGI entry point
    ├── CreateUser/       # App: Auth, Dashboard, Recipients, Groups
    │   ├── views.py      # Core logic
    │   ├── models.py     # DB Models (emailUsers, Receipent, etc.)
    │   └── utils.py      # Helpers (Email sending, File parsing)
    ├── EmailTemplates/   # App: Template Management
    └── Home/             # App: Landing pages
```

---

## Getting Started

### Prerequisites

*   **Python 3.10** or higher
*   **pip** (Python Packet Manager)
*   **Git**

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Mehta-g1/Bulk-Email-Sending-System.git
    cd Bulk-Email-Sending-System
    ```

2.  **Create a virtual environment:**
    ```bash
    # Windows
    python -m venv .venv
    .venv\Scripts\activate

    # macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Environment Setup

Create a `.env` file in the `Email` directory (same level as `manage.py` is usually fine, or inside the inner `Email` config folder depending on how you run it, but standard practice is project root or inner folder. *Note: The settings.py looks for .env in usage with python-decouple*).

**Required `.env` Variables:**

```ini
# Security
SECRET_KEY=your-secure-random-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# System Email (Used for Password Resets & Welcome Emails)
# This is the "Admin" email address. Users will use their OWN credentials for sending campaigns.
EMAIL_HOST_USER=admin-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

4.  **Apply Migrations:**
    ```bash
    cd Email
    python manage.py migrate
    ```

5.  **Run Server:**
    ```bash
    python manage.py runserver
    ```
    Access the app at `http://127.0.0.1:8000/`.

---

## User Guide

### Authentication
*   **Sign Up**: Create an account with Name, Email, Phone.
*   **Login**: Access your private dashboard.
*   **Forgot Password**: Secure reset link sent to your registered email. 
    *   *Note: This system email is sent using the credentials in `.env`.*

### Dashboard & Analytics
Once logged in, the dashboard provides a snapshot of your recipients. You can use the **Search Bar** to filter recipients by name, email, or group.

### Group Management
Go to **View Profile -> Groups**.
*   **Create Group**: Add a new tag (e.g., "HR Dept").
*   **Filter**: On the dashboard, use the dropdown to view recipients only from specific groups.

### Recipient Management
You can add recipients in two ways:

1.  **Manually**: Enter Name, Email, Group, and Category one by one.
2.  **Bulk Upload**: Upload a CSV or Excel file.
    *   **Smart Matching**: The system looks for headers like `Name`, `Fullname`, `Email`, `Mail`.
    *   **Duplicate Check**: Automatically skips emails that are already in your list.
    *   **File History**: View uploaded files and their extraction status in your Profile.

### Template System
Navigate to **Templates**.
*   Create rich text emails (Subject + Body).
*   **Primary Template**: Mark one template as primary to be auto-selected when sending quick emails.

### SMTP Configuration (BYOS)
**Critical Step for Sending:**
1.  Go to **View Profile -> Account Settings**.
2.  Enter **your personal** Email, Password (App Password recommended), Host (e.g., `smtp.gmail.com`), and Port (`587`).
3.  The system uses *these* credentials to send your bulk campaigns, ensuring high deliverability and personal branding.

### Sending Emails
1.  On the Dashboard, check the boxes next to the recipients you want to contact.
2.  (Optional) Select "All" or filter by a Group first.
3.  Click **Send Email**.
4.  The system uses your **Primary Template** and your **Account Settings** SMTP to dispatch the mails.

---

## API & URL Map

| Endpoint | Function |
| :--- | :--- |
| `/` | Landing Page |
| `/user/login/` | User Login |
| `/user/dashboard/` | Main User Dashboard |
| `/user/receipient/add/` | Add Single Recipient |
| `/user/receipient/bulk-add/` | Upload CSV/Excel |
| `/user/templates/` | Manage Templates |
| `/user/group/create/` | Create New Group |
| `/user/account-settings/` | **SMTP Config Page** |
| `/user/submit-form/` | Action Handler (Send/Delete) |

---

## Future Improvements

*   **HTML Rich Text Editor**: Integrate a WYSIWYG editor for templates (e.g., CKEditor).
*   **Scheduled Sending**: Cron jobs to send emails at specific times.
*   **Open Tracking**: Pixel tracking to see if recipients opened the email.
*   **Unsubscribe Link**: Auto-inject footer links for compliance.

---

## Contributing

Contributions are welcome!
1.  Fork the Project.
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the Branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.