# Scan2Eat - Cashless Mess Management System

A full-stack web application for cashless mess management in university hostels, built with Flask (Python), PostgreSQL, and modern JavaScript.

## Features

### Admin Features
- **Dashboard** with real-time statistics and interactive charts
- **Student Registration** with live form validation and preview
- **QR Code Generation** automatic generation using roll number
- **Wallet Management** add balance to student wallets
- **Meal Management** add and manage daily meals
- **QR Code Scanner** real-time camera-based scanning
- **Reports & Analytics** with charts, filters, and CSV export
- **Student Search** instant AJAX-based search

### Student Features
- **Dashboard** with wallet balance and recent transactions
- **Profile** with QR code display
- **Wallet** transaction history
- **Attendance** meal attendance history
- **Meals** view available meals

## Tech Stack

### Backend
- **Python 3.8+** with Flask framework
- **PostgreSQL** database
- **SQLAlchemy** ORM
- **Flask-Login** session management
- **bcrypt** password hashing

### Frontend
- **HTML5** semantic markup
- **CSS3** with custom animations
- **Bootstrap 5** responsive framework
- **JavaScript ES6+** modern JavaScript
- **Chart.js** interactive charts
- **ZXing** QR code scanning

## JavaScript Features

The application includes comprehensive JavaScript functionality:

### Utility Functions (`main.js`)
- Currency and date formatting
- Debounced API calls
- Loading state management

### Toast Notifications
- Success, error, warning, info types
- Auto-dismiss with animation
- Bootstrap-styled

### Form Validation
- Real-time input validation
- Password strength indicator
- Roll number availability check
- Live preview for forms

### Dashboard Charts
- Meal attendance distribution (Doughnut)
- Weekly revenue (Bar chart)
- Attendance trends (Line chart)
- Auto-refresh every 30 seconds

### Student Management
- AJAX-based search
- Quick student details modal
- Balance management

### Data Tables
- Sortable columns
- Client-side filtering
- Click-to-sort headers

### Reports
- Interactive date filters
- Quick presets (Today, Week, Month)
- CSV export functionality
- Print-friendly layout

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/check-roll-number` | GET | Check if roll number exists |
| `/api/students/search` | GET | Search students |
| `/api/students/<id>` | GET | Get student details |
| `/api/students/add-balance` | POST | Add balance to wallet |
| `/api/meals/<id>` | DELETE | Delete a meal |
| `/api/meals/<id>/toggle` | POST | Toggle meal status |
| `/api/stats/dashboard` | GET | Dashboard statistics |
| `/api/stats/meal-attendance` | GET | Meal attendance stats |
| `/api/stats/revenue` | GET | Revenue statistics |
| `/api/stats/weekly-trend` | GET | Weekly attendance trend |
| `/api/reports/export` | GET | Export report as CSV |

## Setup Instructions

### Option 1: Docker Setup (Recommended)

The easiest way to run the application is using Docker.

#### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed

#### Quick Start
```bash
# Clone/copy the project and navigate to the folder
cd scan2eat

# Start the application
docker-compose up --build
```

This single command will:
1. Create PostgreSQL database `scantoeat`
2. Build the Flask application
3. Initialize database tables with default admin
4. Start the web server

#### Access the Application
Open your browser: `http://localhost:5000`

#### Docker Commands
```bash
# Start in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop containers
docker-compose down

# Stop and remove all data (fresh start)
docker-compose down -v

# Rebuild after code changes
docker-compose up --build
```

---

### Option 2: Deploy on Render (Cloud Hosting)

Deploy the application to Render for free cloud hosting.

#### Prerequisites
- [GitHub](https://github.com) account
- [Render](https://render.com) account (free)

#### Method 1: One-Click Deploy (Blueprint)

1. Push this project to a GitHub repository
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **New** → **Blueprint**
4. Connect your GitHub repository
5. Render will automatically detect `render.yaml` and create:
   - PostgreSQL database (`scantoeat`)
   - Web service with your Flask app
6. Wait for deployment to complete (~5-10 minutes)
7. Access your app at: `https://scantoeat.onrender.com`

#### Method 2: Manual Setup on Render

**Step 1: Create PostgreSQL Database**
1. Go to Render Dashboard → **New** → **PostgreSQL**
2. Configure:
   - Name: `scantoeat-db`
   - Database: `scantoeat`
   - User: `scantoeat`
   - Region: Oregon (or closest to you)
   - Plan: Free
3. Click **Create Database**
4. Copy the **External Database URL**

**Step 2: Create Web Service**
1. Go to Render Dashboard → **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - Name: `scantoeat`
   - Runtime: Python
   - Build Command: `./build.sh`
   - Start Command: `gunicorn app:app`
4. Add Environment Variables:
   - `DATABASE_URL` = (paste External Database URL from Step 1)
   - `SECRET_KEY` = (click Generate)
   - `FLASK_DEBUG` = `false`
5. Click **Create Web Service**

#### Default Login
- Username: `admin`
- Password: `admin123`

---

### Option 3: Manual Setup (Local Development)

#### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Modern web browser

#### 1. Create PostgreSQL Database
```sql
CREATE DATABASE scantoeat;
```

#### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment
```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your database credentials
DATABASE_URL=postgresql://username:password@localhost:5432/scantoeat
SECRET_KEY=your-secret-key-here
```

#### 5. Initialize Database
```bash
python init_db.py
```

#### 6. Run the Application
```bash
python app.py
```

#### 7. Access the Application
Open your browser and go to: `http://localhost:5000`

## Default Admin Credentials
- **Username**: admin
- **Password**: admin123

**Important**: Change the admin password after first login!

## Project Structure
```
scan2eat/
├── app.py                  # Main Flask application with routes
├── config.py               # Configuration settings
├── models.py               # SQLAlchemy database models
├── init_db.py              # Database initialization script
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker image configuration
├── docker-compose.yml      # Docker services orchestration
├── .dockerignore           # Docker build exclusions
├── render.yaml             # Render deployment blueprint
├── build.sh                # Render build script
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore file
├── README.md               # This file
├── static/
│   ├── css/
│   │   └── style.css       # Custom styles with animations
│   ├── js/
│   │   └── main.js         # Main JavaScript file
│   └── qr_codes/           # Generated QR codes
└── templates/
    ├── base.html           # Base template with navigation
    ├── login.html          # Login page
    ├── admin/
    │   ├── dashboard.html  # Admin dashboard with charts
    │   ├── register_student.html
    │   ├── students.html
    │   ├── wallet.html
    │   ├── meals.html
    │   ├── scan.html       # QR scanner with camera
    │   └── reports.html    # Reports with charts
    ├── student/
    │   ├── dashboard.html
    │   ├── profile.html
    │   ├── wallet.html
    │   ├── attendance.html
    │   └── meals.html
    └── errors/
        ├── 404.html
        └── 500.html
```

## Usage

### For Admin:
1. Login with admin credentials
2. Register students with their details
3. Add meals for each day (breakfast, lunch, dinner)
4. Use the Scan QR feature to mark attendance
5. View reports and analytics

### For Students:
1. Login with roll number and password
2. View your QR code in the Profile section
3. Show QR code at mess during meal time
4. Track your wallet balance and transactions

## Browser Compatibility
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## License
MIT License
