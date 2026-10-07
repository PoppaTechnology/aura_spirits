# Aura Spirits: Luxury Cellar & Premium Beverage Platform

[![Django](https://img.shields.io/badge/Django-6.1.1-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

**Aura Spirits** is a modern e-commerce web platform and digital cellar registry designed for fine spirit collections. Built with Django and modern frontend technologies, the platform offers an intuitive catalog, real-time shopping cart and wishlist management, tasting profiles, and a concierge order settlement workflow.

---

## Table of Contents

- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation & Setup](#installation--setup)
  - [Running the Server](#running-the-server)
- [Running Tests](#-running-tests)
- [License](#-license)

---

## Key Features

- **Curated Spirits Catalog**: High-resolution bottle views, specifications, and sensory tasting notes (Nose, Palate, Finish).
- **Dynamic Filtering & Search**: Instant filtering by spirit category, price range, and custom collections.
- **Real-Time Cellar Cart**: Seamless AJAX-driven cart updates, slide-over drawer, and free courier delivery progress indicator.
- **VIP Voucher Support**: Apply exclusive promotional discount codes directly during cart review or checkout.
- **Wishlist**: Save favorite bottles to your personal collection.
- **Concierge Order Settlement**: Unique Order Ticket IDs for private allocations and courier coordination.
- **Tasting Reviews**: Community ratings and tasting notes.

---

## Tech Stack

- **Backend**: Django 6.1+ (Python 3.12+)
- **Database**: SQLite (Development) / PostgreSQL compatible
- **Frontend**: HTML5, Vanilla JavaScript (ES6+), Custom Vanilla CSS
- **Design System**: Responsive Dark Luxe theme with Glassmorphism
- **Icons & Fonts**: Phosphor Icons, Google Fonts (Cormorant Garamond & Inter)

---

## Project Structure

```text
aura_spirits/
│
├── aura_spirits_config/         # Core Django configuration & settings
├── store/                       # Store application
│   ├── models.py                # Database models (Products, Orders, Coupons, Reviews)
│   ├── views.py                 # Views and AJAX endpoints
│   ├── urls.py                  # URL routing
│   ├── cart.py                  # Cart logic & calculations
│   ├── admin.py                 # Admin dashboard configurations
│   └── tests.py                 # Test suite
│
├── static/                      # Static assets
│   ├── css/custom.css           # Styling & theme variables
│   └── js/custom.js             # AJAX interactions & drawer handlers
│
├── templates/                   # HTML templates
│   ├── base.html                # Base layout
│   └── store/                   # Storefront, catalog, cart, and checkout views
│
├── manage.py                    # Django CLI
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

---

##  Getting Started

### Prerequisites

- Python 3.10+
- `pip` package manager

### Installation & Setup

1. **Clone the repository and navigate into the folder**:
   ```bash
   git clone <repository_url>
   cd aura_spirits
   ```

2. **Create and activate a virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply database migrations**:
   ```bash
   python manage.py migrate
   ```

5. **(Optional) Create an admin superuser**:
   ```bash
   python manage.py createsuperuser
   ```

### Running the Server

Start the local development server:

```bash
python manage.py runserver
```

Visit the application in your browser:
- **Storefront**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Admin Portal**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## Running Tests

To run the automated test suite:

```bash
python manage.py test
```

---

## License

&copy; 2026 Aura Spirits. All rights reserved.
