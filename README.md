# 📧 EmailAuto: Advanced Email Automation & API Ecosystem

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org)
[![Django Version](https://img.shields.io/badge/django-5.2+-green.svg)](https://www.djangoproject.com)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

**EmailAuto** is a comprehensive, full-stack email marketing and developer-centric automation platform. Developed as an **Advanced BCA Major Project**, it bridges the gap between simple email scripts and professional communication tools by offering high-concurrency multi-threading, deep engagement analytics, and a powerful REST API.

---

## 📑 Table of Contents

1. [Executive Summary](#-executive-summary)
2. [Feature Deep-Dive](#-feature-deep-dive)
3. [System Architecture](#-system-architecture)
4. [Data Model &amp; Relationships](#-data-model--relationships)
5. [Internal Workflow &amp; Logic](#-internal-workflow--logic)
6. [API Documentation](#-api-documentation)
7. [Installation &amp; Deployment](#-installation--deployment)
8. [Comprehensive Screenshots Guide](#-comprehensive-screenshots-guide)

---

## 🚀 Executive Summary

EmailAuto is designed for developers and businesses that require **control**, **speed**, and **intelligence**. Unlike standard tools, it allows for custom SMTP rotation, provides raw engagement data, and handles thousands of recipients without blocking the user interface.

---

## 💎 Feature Deep-Dive

### 📡 Multi-Threaded Campaign Engine

The heart of the platform is a dynamic threading engine that optimizes itself based on the workload:

* **Dynamic Scaling**: For lists larger than 10, the system automatically spawns up to 5 concurrent threads.
* **Asynchronous Backgrounding**: All campaigns are moved to a background worker immediately upon initiation. This prevents request timeouts and allows the user to navigate the site while sending occurs.
* **SMTP Connection Pooling**: Reuses connections across threads to minimize the handshake overhead with providers like Gmail or Outlook.

### 📊 Engagement Intelligence

* **Zero-Latency Tracking**: Tracking links and pixels are processed in milliseconds to ensure zero impact on recipient load times.
* **Link Rewriting Engine**: A custom regex-based parser that identifies all `<a>` tags in your HTML and wraps them in unique tracking redirects.
* **Open Rate Analysis**: Uses 1x1 transparent GIF injection to detect "Seen" status.

### 🧠 Smart Data Intake

* **Heuristic Column Detection**: Our Pandas-powered engine scans column content to find email addresses and names, even if the file has no headers.
* **Bulk Operations**: Support for `.csv`, `.xls`, and `.xlsx` with automatic duplicate detection and data sanitization.

---

## 🏗️ System Architecture

The platform follows a modular **Service-Oriented Architecture (SOA)**:

| Module                                  | Responsibility                                               |
| :-------------------------------------- | :----------------------------------------------------------- |
| **`services/email_service.py`** | Handles threading, SMTP logic, and campaign orchestration.   |
| **`tracking/`**                 | Handles incoming pixel hits and link redirects.              |
| **`api/`**                      | Exposes core functionality to external developers via REST.  |
| **`campaigns/`**                | Stores snapshots of sent content, stats, and recipient logs. |

---

## 🧬 Data Model & Relationships

The database is designed with a hierarchical relationship to ensure data integrity and trackability.

### Entity Relationship Overview:

1. **`emailUsers` (The Center)**:
   * `1 : N` with `Receipent_Group`: A user can have multiple groups.
   * `1 : N` with `Template`: A user can design multiple email templates.
   * `1 : N` with `Campaign`: A user can launch many campaigns.
2. **`Receipent_Group`**:
   * `1 : N` with `Receipent`: A group contains many recipients.
3. **`Campaign`**:
   * `1 : N` with `EmailLog`: Each campaign generates a log for every recipient it targeted.
4. **`EmailLog`**:
   * `1 : 1` link to a unique tracking UUID for open/click events.

### Database Connection Philosophy:

While the project currently uses **SQLite** for development (zero-config), the models are written using **Django ORM**, making it "DB Agnostic." You can switch to **PostgreSQL** or **MySQL** by simply updating the `DATABASES` setting in `settings.py`. All complex queries (like analytics aggregation) use Django's `F` expressions and `Count` aggregates to ensure performance across different database engines.

---

## 🔄 Internal Workflow & Logic

### 1. The Sending Lifecycle

1. **Request**: User selects a group and template.
2. **Snapshot**: The system takes a "Content Snapshot" of the template (Subject/Body).
3. **Log Generation**: `EmailLog` records are pre-generated in a `Pending` state.
4. **Distribution**: The `ThreadPoolExecutor` picks up tasks. Each thread handles its own placeholders (`{{name}}`, etc.).
5. **Tracking**: As emails are opened/clicked, the `tracking` app updates logs in real-time.

---

## 🔌 API Documentation

### Authentication

Include your API Key in the header: `X-API-KEY: your_generated_key`

### Endpoint: Send Bulk Email

`POST /api/v1/send-bulk/`

```json
{
  "template_id": 12,
  "recipient_ids": [101, 102, 103],
  "campaign_name": "Product Launch"
}
```

---

## 📸 Comprehensive Screenshots Guide

*To complete this README, replace the text below with actual images.*

### 1. Unified Dashboard

> ![Home Page](screenshots/home.png)
> *Key View: Global analytics charts and quick-action buttons.*

### 2. Campaign Deep-Dive & Tracking

> ![Home Page](screenshots/campaigns_deep.png)
> *Key View: Real-time progress bars and engagement metrics.*

### 3. Template Editor & Personalization

> ![Placeholder: Rich text editor showing {{name}} placeholders](screenshots/template_editor.png)
> *Key View: Designing responsive HTML templates.*

### 4. Sent Content Snapshot

> ![Placeholder: The fixed snapshot of the email body as it was sent](screenshots/delivered.jpeg)
> *Key View: Proof of exactly what was delivered to customers.*

### 5. API & SMTP Configuration

> ![Placeholder: API key generation and SMTP provider settings](screenshots/api_configure.png)
> *Key View: Configuring Gmail/Zoho/Outlook credentials.*

---

## ⚙️ Installation & Setup Guide

Follow these steps to get the platform running on your local machine.

### 1. Clone the Repository

```bash
git clone <repository-url>
cd EmailAuto
```

### 2. Set Up Virtual Environment

Creating a virtual environment ensures that the project dependencies don't conflict with other Python projects on your system.

**On Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the `Email/` directory (where `settings.py` is located) and add your secret key and database settings:

```text
SECRET_KEY=your-very-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

### 5. Database Setup

Apply migrations to create the database schema:

```bash
# Navigate to the project folder
cd Email

# Run migrations
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Admin Account

Create a superuser to access the Django Admin and the platform dashboard:

```bash
python manage.py createsuperuser
```

### 7. Run the Development Server

```bash
python manage.py runserver
```

Once started, visit `http://127.0.0.1:8000` in your browser.

---

**© 2025 EmailAuto Platform. Optimized for performance and deliverability.**
