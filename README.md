# AI-Based Drug-Food Interaction Predictor

A modern React + FastAPI application for predicting medication-food interactions.

## What changed
- The old backend has been replaced by FastAPI.
- The application is now powered exclusively by FastAPI.
- The React frontend communicates directly with the FastAPI backend on `http://localhost:8000/api` in development.
- Production frontend builds are served from FastAPI via `backend_api/main.py`.

## Tech Stack
- **Frontend**: React.js, Vite, Framer Motion, Lucide React
- **Backend**: FastAPI, SQLAlchemy, SQLite, XGBoost, RDKit
- **HTTP Client**: Axios
- **Styling**: Vanilla CSS

---

## 📁 Updated Project Structure

```
AI DRUG FOOD/
├── src/                               # React Frontend
│   ├── components/
│   │   ├── Interaction/
│   │   ├── Navbar/
│   │   └── InteractionExample.jsx
│   ├── pages/
│   ├── services/
│   │   ├── api.js
│   │   └── interactionApi.js
│   ├── context/
│   └── App.jsx
├── backend_api/                       # FastAPI backend
│   ├── main.py
│   ├── requirements.txt
├── package.json                       # Frontend dependencies
├── vite.config.js
├── .env                               # Frontend env variables
└── README.md
```

---

## 🚀 Quick Start - FastAPI Backend

### Prerequisites
- Node.js v16+ and npm
- Python 3.9+ and pip

### Step 1: Install frontend dependencies
```bash
npm install
```

### Step 2: Install backend dependencies
```bash
cd backend_api
pip install -r requirements.txt
cd ..
```

### Step 3: Start backend
```bash
cd backend_api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Backend will run on: **http://localhost:8000**

### Step 4: Start frontend
```bash
npm run dev
```
Frontend will run on: **http://localhost:3000**

If you need to run the frontend against the backend on a different URL, update `VITE_API_URL` in `.env`.

---

## 🔧 Backend details

### `backend_api/main.py`

This unified FastAPI backend includes:
- CORS middleware for React dev server communication
- SQLAlchemy + SQLite persistence for interactions and history
- `/api/interactions` CRUD routes
- `/api/search` search route
- `/api/predict` ML prediction route
- `/api/history` history fetch/log routes
- static file serving of the React `dist/` build folder

### Production build
Run:
```bash
npm run build
```
Then start FastAPI and it will serve the compiled React app if `dist/` exists.

---

## 📡 HTTP API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Backend health check |
| GET | `/api/interactions` | List all interactions |
| GET | `/api/interactions/{id}` | Get interaction by ID |
| POST | `/api/interactions` | Create interaction |
| PUT | `/api/interactions/{id}` | Update interaction |
| DELETE | `/api/interactions/{id}` | Delete interaction |
| GET | `/api/search` | Search interactions by drug and/or food |
| POST | `/api/predict` | Predict drug-food interaction |
| GET | `/api/history` | List saved prediction history |
| POST | `/api/history` | Log a prediction history item |

---

## Environment configuration

### Frontend dev server
Set:
```env
VITE_API_URL=http://localhost:8000/api
```

### Backend model and dataset configuration
Optional environment variables for `backend_api/main.py`:
```env
MODEL_PATH=drug_food_model.json
DRUG_DATASET_PATH=drug_dataset.csv
FOOD_DATASET_PATH=food_dataset.csv
DATABASE_URL=sqlite:///backend_api/app.db
```

If your dataset or model files live elsewhere, update those variables before starting the FastAPI backend.

### FastAPI Backend (http://localhost:8000/api)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/interactions` | Get all interactions |
| GET | `/interactions/{id}` | Get single interaction |
| POST | `/interactions` | Create new interaction |
| PUT | `/interactions/{id}` | Update interaction |
| DELETE | `/interactions/{id}` | Delete interaction |
| GET | `/search` | Search interactions |
| GET | `/health` | Health check |

---

## 💻 Example API Usage

### Using React with Axios

```jsx
import { getInteractions, createInteraction } from './services/interactionApi';

// Fetch all interactions
const fetchData = async () => {
  try {
    const response = await getInteractions();
    console.log(response.data);
  } catch (error) {
    console.error('Error:', error);
  }
};

// Create new interaction
const addInteraction = async () => {
  const newData = {
    drug: 'Aspirin',
    food: 'Alcohol',
    severity: 'High',
    description: 'Increases bleeding risk'
  };
  try {
    const response = await createInteraction(newData);
    console.log('Created:', response.data);
  } catch (error) {
    console.error('Error:', error);
  }
};
```

### Using Python Requests with FastAPI

```python
import requests

# Fetch all interactions
response = requests.get('http://localhost:8000/api/interactions')
print(response.json())

# Create new interaction
data = {
    'drug': 'Aspirin',
    'food': 'Alcohol',
    'severity': 'High',
    'description': 'Increases bleeding risk'
}
response = requests.post('http://localhost:8000/api/interactions', json=data)
print(response.json())
```

### Using cURL

```bash
# GET all interactions
curl http://localhost:8000/api/interactions

# POST new interaction
curl -X POST http://localhost:8000/api/interactions \
  -H "Content-Type: application/json" \
  -d '{
    "drug": "Aspirin",
    "food": "Alcohol",
    "severity": "High",
    "description": "Increases bleeding risk"
  }'

# DELETE interaction
curl -X DELETE http://localhost:8000/api/interactions/1
```

---

## ⚙️ Environment Configuration

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000/api
```

### FastAPI Backend (backend_api/.env)
```env
PORT=8000
DEBUG=True
DATABASE_URL=your_database_url
```

---

## 📊 Example Component

See `src/components/InteractionExample.jsx` for a complete working example with:
- Form to add interactions
- Display all interactions in a table
- Delete functionality
- Search feature

---

## 🐛 Troubleshooting

### CORS Errors
**FastAPI:** Add CORS middleware in `backend_api/main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Port Already in Use
**FastAPI:** Run on a different port: `python main.py --port 8001`
**Frontend:** Vite will use the next available port

### Dependency Issues

**Node.js:**
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**Python:**
```bash
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Frontend Can't Connect to Backend
- Verify backend is running on correct port
- Check `VITE_API_URL` in `.env`
- Check browser console for error messages
- Verify CORS is enabled on backend

---

## 📦 Installation Summary

### Quick Setup (FastAPI)
```bash
# Frontend
npm install

# Backend
cd backend_api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..

# Run in 2 terminals
terminal 1: cd backend_api && python main.py
terminal 2: npm run dev (with VITE_API_URL=http://localhost:8000/api)
```

---

## 📤 Version Control

### Initial Push to GitHub
```bash
git add .
git commit -m "Initial commit: Add React frontend and FastAPI backend"
git push origin main
```

### After Making Changes
```bash
git add .
git commit -m "Describe your changes"
git push origin main
```

---

## 🎓 Next Steps

1. **Database Integration**: Replace mock data with MongoDB, PostgreSQL, or Firebase
2. **Authentication**: Add JWT or OAuth2 authentication
3. **Validation**: Implement input validation and error handling
4. **Deployment**: Deploy to Vercel (frontend), Heroku or Railway (backend)
5. **Testing**: Add unit and integration tests
6. **Documentation**: Add API documentation with Swagger/OpenAPI

---

## 📚 Resources

- [React Documentation](https://react.dev)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Vite Guide](https://vitejs.dev)
- [Axios Documentation](https://axios-http.com)

---

## License
This project is licensed under the MIT License.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📞 Support

For issues or questions, please open a GitHub issue or contact the maintainers.

Happy Coding! 🚀

