💄 Beauty Dupe Finder
A Flask-based web application that helps users discover affordable beauty product alternatives (dupes) by searching for existing products. Includes an admin panel for managing products, images, and dupe relationships.

🚀 Live Demo
🔗 https://beauty-dupe-search.onrender.com
🛠️ Admin Password: admin123

📌 Features
🔍 Dupe Search
General Search: Match brand or product names (case-insensitive, partial).

Specific Search: Exact match returns original product and sorted dupes (by price).

Dupe Matching Logic: Products with lower price linked to original, sorted by cheapest first.

🛠️ Admin Panel
Password-protected route: /admin (admin123)

Add/edit/delete products and images

Link dupes manually

Prevents linking products to themselves

Session-based authentication with flash messaging

🏗️ Tech Stack
Layer	Technology
Backend	Python (Flask)
Database	SQLite
Frontend	HTML, CSS (Jinja)
File Upload	Werkzeug (local)
Deployment	Gunicorn + Render

🗂️ Project Structure
bash
Copy
Edit
beauty-dupes/
├── app.py                  # Main Flask app
├── templates/              # HTML templates
│   ├── index.html
│   ├── search_results.html
│   ├── admin.html
│   └── edit_product.html
├── static/uploads/         # Uploaded product images
├── dupes.db                # SQLite database
├── requirements.txt
├── .gitignore
└── README.md
🧠 Database Schema
products Table
Column	Type	Description
id	INTEGER	Primary key
brand	TEXT	Brand name
name	TEXT	Product name
color	TEXT	Optional color/shade
price	REAL	Price (INR)
image	TEXT	Image filename

dupes Table
Column	Type	Description
id	INTEGER	Primary key
original_id	INTEGER	FK to products.id (original)
dupe_id	INTEGER	FK to products.id (alternative)

🔒 Routes Summary
Route	Method	Description
/admin	GET/POST	Admin login + dashboard
/admin/logout	GET	Logout admin
/admin/add-product	POST	Add a new product
/admin/edit-product/<id>	GET/POST	Edit product and manage dupes
/admin/delete-product/<id>	POST	Delete a product and its dupes
/admin/link-dupe	POST	Link a product as a dupe
/search	GET	General and specific search results

🔧 How to Run Locally
Clone the repository

bash
Copy
Edit
git clone https://github.com/shivansshhhh/beauty-dupe-search.git
cd beauty-dupe-search
Create a virtual environment and activate it

bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
Install dependencies

nginx
Copy
Edit
pip install -r requirements.txt
Run the application

nginx
Copy
Edit
python app.py
Visit: http://localhost:5000

🧱 Future Enhancements
🔍 Barcode Search — Match products by barcode for faster lookup.

🔐 User Authentication — Register/log in users with Flask-Login or OAuth.

🧠 Smarter Matching — Use ML and fuzzy matching for better dupe suggestions.

⭐ Reviews & Ratings — Users can rate and review products.

🌩️ Cloud Image Hosting — Migrate uploads to S3 or Cloudinary.

📱 API Support — Expose search endpoints for mobile app integration.

📦 Deployment Notes
Ideal for Render, Fly.io, or Heroku

Use Gunicorn in production (add a Procfile)

Images are stored locally — may not persist across redeploys

Consider moving to PostgreSQL + cloud image storage for scalability

📬 Contact
