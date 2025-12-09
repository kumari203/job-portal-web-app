Project Title:Job Portal Web Application (Flask + SQLAlchemy + Bootstrap)
Project Overview:A full-stack Job Portal where employers can post jobs and job seekers can search, apply, and manage applications and users.
The project is built using Flask, SQLAlchemy, HTML, CSS, and Bootstrap.
Features:
1.User Authentication
  Register (Admin / Employer / Job Seeker)
  Login / Logout
  Forgot & Reset Password
2.Employer Features
  Post new job listings
  Edit and manage existing jobs
  View number of job applications
3.Job Seeker Features
  Search for jobs 
  Apply to jobs
4.Admin Features
  Manage all users
  Manage job listings
Tech Stack:
Backend: Python(Flask)
Frontend: HTML,CSS, Bootstrap
Database: SQLite
Project Structure:
Job_Portal_Web_Application/
│
├── app.py
├── requirements.txt
├── .gitignore
│
├── migrations/
│   └── ... (Flask-Migrate auto-generated files)
│
├── templates/
│   ├── base.html
│   ├── index.html
│   │
│   ├── login.html
│   ├── register.html
│   ├── forgot_password.html
│   ├── reset_password.html
│   │
│   ├── employer_dashboard.html
│   ├── jobseeker_dashboard.html
│   ├── admin_dashboard.html
│   │
│   ├── post_job.html
│   ├── edit_job.html
│
└── README.md 
How to Run Locally:
1️⃣ Clone the repository
git clone https://github.com/yourusername/job-portal-web-app.git
cd job-portal-web-app

2️⃣ Create virtual environment
python -m venv venv
For activation:
venv\Scripts\activate # Windows
source venv/bin/activate # Mac / Linux

3️⃣ Install dependencies
pip install -r requirements.txt

4️⃣ Run database migrations
flask db upgrade
(Or use)
python app.py

5️⃣ Start the application
flask run
(Or use)
python app.py
Open the app in your browser by entering below link
http://127.0.0.1:5000
### Create a .env file

Create a .env file in the project root and add:

SECRET_KEY=your_secret_key_here
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_password(app password if gmail )
📸 Screenshots
Below are the screenshots of the Job Portal Web Application.
👨‍💼 Admin Dashboard
Admin Dashboard – View 1
![Admin Dashboard 1](assets/Admin dashboard1.png)

Admin Dashboard – View 2
![Admin Dashboard 2](assets/Admin dashboard2.png)

🧑‍💼 Employer Interface
Employer Dashboard
![Employer Dashboard](assets/Employer dashboard.png)

New Job Posting – Page 1
![New Job Posting Page 1](assets/New job posting page1.png)

New Job Posting – Page 2
![New Job Posting Page 2](assets/New job posting page2.png)

Job Editing – Page 1
![Job Editing Page 1](assets/Job editing page1.png)

Job Editing – Page 2
![Job Editing Page 2](assets/Job editing page2.png)

👤 Job Seeker Interface
Job Seeker Dashboard
![Job Seeker Dashboard](assets/Job seeker dashboard.png)

🔐 Authentication Screens
Login Page
![Login Page](assets/Login Page.png)

Register Page – Step 1
![Register Page 1](assets/Register Page1.png)

Register Page – Step 2
![Register Page 2](assets/Register Page2.png)




