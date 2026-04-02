## ⚙️ SETUP INSTRUCTIONS

### 1. Clone the repository
git clone repo-url  
cd project-folder

### 2. Create a virtual environment
python -m venv .venv  
source .venv/bin/activate

#### On Windows:
.venv\Scripts\activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Create a .env file in the project root
touch .env

### 5. Add the following to your .env file
SECRET_KEY=your_django_secret_key  
EMAIL_HOST_USER=your_gmail@gmail.com  
EMAIL_HOST_PASSWORD=your_gmail_app_password

### 6. Run migrations
python manage.py migrate

### 7. Run the development server:
   python manage.py runserver
