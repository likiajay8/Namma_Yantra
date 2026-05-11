🚜 Namma-Yantra Share
📌 Project Overview

Namma-Yantra Share is a web-based platform designed to help small farmers rent agricultural machinery like tractors, harvesters, and sprayers.

It works as a peer-to-peer rental system, similar to an "Uber for tractors", where:

Owners list their machines
Customers can browse and request machines nearby

👉 This project is specifically designed for Bangalore (Bengaluru).
The backend (app.py) includes major Bangalore areas like Whitefield, Hoskote, KR Puram, Devanahalli, and Chikkabanavara with their latitude and longitude for distance-based sorting.

🚀 Features

🔐 User Authentication

Login using mobile number

OTP system (OTP = last 4 digits of mobile number)

➕ Add Machine

Add machine details:

Name

Machine Company

Price per hour

Location (Bangalore areas)

Condition

Select service options:

🚚 Delivery (owner delivers machine)

📍 Pickup (customer collects machine)

🔍 Browse Machines

View available machines in Bangalore

Machines added by the logged-in user are hidden from their own view

Sort options:

💰 Sort by Price

📍 Sort by Distance (based on user location)

🧑‍🌾 My Machines

View machines added by the logged-in user

Toggle availability:

✅ ON → visible to customers

❌ OFF → hidden from browse

Shows all details except location

🛒 Request / Order Flow (Cart-like System)

User selects a machine → goes to request page

Enter number of hours

System calculates total price

Select service mode:

Delivery or Pickup
Click Confirm Order to place request

👉 Payment is not implemented (demo purpose), but total cost is displayed.

📦 Orders System
Customers can request machines
Owners can view requests in My Orders
Each order shows:
Machine name
Customer mobile number
Duration (hours)
Delivery/Pickup mode
🛠️ Tech Stack
Backend: Python (Flask)
Frontend: HTML, CSS, Jinja2
Database: SQLite
Location Logic: Haversine Formula
📂 Project Structure
project/
│
├── app.py
├── database.db
├── templates/
│   ├── home.html
│   ├── login.html
│   ├── list.html
│   ├── browse.html
│   ├── request.html
│   ├── my_machines.html
│   ├── orders.html
│
└── static/
⚙️ Installation & Setup
1. Clone the repository
git clone <your-repo-link>
cd project
2. Create virtual environment
python -m venv venv
3. Activate environment
venv\Scripts\activate
4. Install Flask
pip install flask
5. Run the app
python app.py
🌐 Usage
Open browser
Go to:
http://127.0.0.1:5000
Login using:
Mobile number
OTP = last 4 digits
🔮 Future Improvements
Live GPS tracking
Payment integration
Real-time notifications
Map-based machine view
Admin dashboard
🎓 Project Type
Academic / Mini Project
Domain: Agriculture + Web Development
💡 Inspiration

This project solves:

Underutilization of agricultural machinery
Lack of access for small farmers
🏁 Final Note

This project demonstrates:

Full-stack development
Real-world problem solving
User-based system design
Location-based services
🚀
