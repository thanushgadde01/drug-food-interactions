# FastAPI + React Backend Setup Guide

## 📁 Project Structure

```
AI DRUG FOOD/
├── src/                          # React Frontend
│   ├── components/
│   │   ├── InteractionExample.jsx # Example component showing API usage
│   │   └── ...
│   ├── services/
│   │   ├── api.js                # Base axios config
│   │   └── interactionApi.js     # API functions for interactions
│   └── ...
├── backend_api/                   # FastAPI Backend
│   ├── main.py                   # Main FastAPI server file
│   ├── requirements.txt
│   ├── .env                      # Environment variables
│   └── ...
├── .env                          # Frontend environment variables
└── ...
```

---

## 🚀 Getting Started

### Step 1: Install Backend Dependencies

```bash
cd backend
npm install
```

### Step 2: Start Backend Server

```bash
cd backend_api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will run on: **http://localhost:8000**

### Step 3: Install Frontend Dependencies

```bash
cd ..
npm install
```

### Step 4: Start Frontend Development Server

```bash
npm run dev
```

The frontend will run on: **http://localhost:5173** (or similar)

---

## 📡 API Endpoints

### Base URL: `http://localhost:8000/api`

### Interactions Endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/interactions` | Get all interactions |
| GET | `/interactions/:id` | Get interaction by ID |
| POST | `/interactions` | Create new interaction |
| PUT | `/interactions/:id` | Update interaction |
| DELETE | `/interactions/:id` | Delete interaction |
| GET | `/search?drug=name&food=name` | Search interactions |

---

## 📝 Example Usage in React

### 1. Fetch All Interactions (GET)

```jsx
import { getInteractions } from '../services/interactionApi';

const MyComponent = () => {
  useEffect(() => {
    const fetchData = async () => {
      const response = await getInteractions();
      console.log(response.data); // Array of interactions
    };
    fetchData();
  }, []);
};
```

### 2. Create Interaction (POST)

```jsx
import { createInteraction } from '../services/interactionApi';

const newInteraction = {
  drug: 'Aspirin',
  food: 'Alcohol',
  severity: 'High',
  description: 'Can increase risk of stomach bleeding'
};

const response = await createInteraction(newInteraction);
console.log(response.data); // Created interaction
```

### 3. Update Interaction (PUT)

```jsx
import { updateInteraction } from '../services/interactionApi';

const updatedData = {
  severity: 'Medium',
  description: 'Updated description'
};

const response = await updateInteraction(1, updatedData);
console.log(response.data); // Updated interaction
```

### 4. Delete Interaction (DELETE)

```jsx
import { deleteInteraction } from '../services/interactionApi';

const response = await deleteInteraction(1);
console.log(response.message); // Success message
```

### 5. Search Interactions (Query)

```jsx
import { searchInteractions } from '../services/interactionApi';

const results = await searchInteractions('Aspirin', 'Alcohol');
console.log(results.data); // Filtered results
```

---

## 🔌 Complete Example Component

See `src/components/InteractionExample.jsx` for a full working example with:
- Form to add interactions
- Display all interactions in a table
- Delete interactions
- Search functionality

---

## ⚙️ Configuration

### FastAPI Backend (backend_api/.env)
```
PORT=8000
DEBUG=True
DATABASE_URL=sqlite:///./app.db
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000/api
```

---

## 📦 Required Dependencies

### Backend
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - ORM for SQLite
- `pydantic` - Data validation
- `python-dotenv` - Environment variables

### Frontend
- `axios` - HTTP client (already in package.json)
- `react` - UI framework
- `react-router-dom` - Routing

---

## 🐛 Troubleshooting

### CORS Error?
Make sure the backend has CORS enabled:
```javascript
app.use(cors());
```

### Port Already in Use?
Stop the process using port 8000 or start the FastAPI backend on a different port (for example `python main.py --port 8001`).

### Frontend can't reach backend?
- Check `VITE_API_URL` in frontend `.env`
- Make sure backend is running on port 8000
- Check browser console for error messages

---

## 📤 Pushing to GitHub

After making changes:

```bash
git add .
git commit -m "Update documentation and FastAPI backend configuration"
git push origin main
```

---

## 🎓 Next Steps

1. Replace mock data with real database (MongoDB, PostgreSQL, etc.)
2. Add authentication (JWT tokens)
3. Add input validation and error handling
4. Deploy to production (Heroku, Vercel, AWS, etc.)
5. Add more complex business logic and endpoints

---

## 💡 Tips

- Use `console.log()` in backend endpoints to debug
- Check browser DevTools Network tab for API requests
- Use Postman to test API endpoints before connecting frontend
- Keep error messages descriptive for debugging

Happy coding! 🚀
