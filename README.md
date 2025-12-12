# AI-Powered Personal Wardrobe & Outfit Recommendation App (Kenya Context)

This is a MERN-like app (FastAPI backend, React frontend, MongoDB) for managing wardrobes with AI classification, visual search, and future outfit recommendations. Tailored for Kenyan users with mitumba and sustainability focus.

# Prerequisites
- Python 3.10+
- Node.js 18+ & Yarn
- MongoDB (local or Atlas)
- Cloudinary account (free)
- Git

# Setup & Installation

# Clone the Repo
git clone https://github.com/Tesla-sudo/AI-WARDROBE-KENYA.git
cd AI-WARDROBE-KENYA

# Backend Setup(Python/FastAPI)
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
# or source venv/bin/activate on macOS/Linux

pip install fastapi uvicorn motor tensorflow opencv-python-headless pillow numpy faiss-cpu cloudinary python-multipart python-dotenv pyjwt

# Create .env in backend/:
MONGO_URI=mongodb://localhost:27017/wardrobe_ai_kenya  # or Atlas URI - create a mongodb atlas account and pick the string
JWT_SECRET=your-very-long-secret-key-2025
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Run backend:
uvicorn main:app --reload --port 8000
Test: http://127.0.0.1:8000/docs (Swagger UI)

# Frontend Setup (React)
cd frontend
npm install

# Create .env.local in frontend/:
VITE_API_URL=http://localhost:8000/api

# Run frontend:
npm start
Test: http://localhost:5173/login → dummy login → upload shirt.jpg

# Running the App

Backend on 8000, frontend on 5173.
Login with dummy token.
Upload images → AI tags category/color.
Visual search → find similar.

# Troubleshooting

MongoDB: Ensure running (mongod).
Cloudinary: Check keys in .env.
Errors: Check terminal for details.