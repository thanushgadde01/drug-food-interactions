import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('medsafe_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ──────────────────────────────────────────────
// BACKEND-CONNECTED INTERACTION SERVICE
// ──────────────────────────────────────────────
export const interactionService = {
  predict: async (drug, food) => {
    try {
      const response = await api.post('/predict', { drug, food });
      return response.data.data;
    } catch (error) {
      console.error('Error predicting interaction:', error);
      const message = error?.response?.data?.message || error.message || 'Prediction failed';
      throw new Error(message);
    }
  },

  getHistory: async () => {
    await new Promise(r => setTimeout(r, 600));
    const raw = localStorage.getItem('medsafe_history');
    return raw ? JSON.parse(raw) : [];
  },

  saveToHistory: (result) => {
    const raw = localStorage.getItem('medsafe_history');
    const history = raw ? JSON.parse(raw) : [];
    history.unshift({ ...result, id: Date.now() });
    localStorage.setItem('medsafe_history', JSON.stringify(history.slice(0, 50)));
  },
};

// ──────────────────────────────────────────────
// MOCK DATA — simulates backend responses for developer preview
// ──────────────────────────────────────────────
const INTERACTIONS_DB = {
  'warfarin': {
    'grapefruit': { risk: 'HIGH', severity: 'Severe', effect: 'Grapefruit inhibits CYP3A4, dramatically increasing warfarin plasma levels, risking dangerous bleeding.', advice: 'Avoid grapefruit entirely while on warfarin. Contact your physician immediately if consumed.' },
    'spinach': { risk: 'MODERATE', severity: 'Moderate', effect: 'Spinach is high in Vitamin K, which opposes warfarin\'s anticoagulant action and can reduce its effectiveness.', advice: 'Maintain a consistent diet of Vitamin K-rich foods rather than avoiding them. Monitor INR closely.' },
    'alcohol': { risk: 'HIGH', severity: 'Severe', effect: 'Alcohol can potentiate warfarin\'s effect, significantly increasing bleeding risk.', advice: 'Avoid alcohol consumption while on warfarin.' },
    'cranberry': { risk: 'MODERATE', severity: 'Moderate', effect: 'Cranberry juice may enhance warfarin\'s anticoagulant effect through CYP2C9 inhibition.', advice: 'Limit cranberry juice intake and monitor INR levels regularly.' },
  },
  'atorvastatin': {
    'grapefruit': { risk: 'HIGH', severity: 'Severe', effect: 'Grapefruit juice inhibits CYP3A4, increasing atorvastatin blood levels up to 83%, raising risk of muscle damage (rhabdomyolysis).', advice: 'Completely avoid grapefruit and grapefruit juice. Switch to a different citrus if desired.' },
    'alcohol': { risk: 'MODERATE', severity: 'Moderate', effect: 'Alcohol increases risk of liver damage when combined with statins.', advice: 'Limit alcohol to no more than 1-2 drinks per day. Avoid heavy drinking entirely.' },
    'dairy': { risk: 'LOW', severity: 'Low', effect: 'Some dairy products may slightly affect statin absorption.', advice: 'Generally safe. No significant restriction needed.' },
  },
  'metformin': {
    'alcohol': { risk: 'HIGH', severity: 'Severe', effect: 'Alcohol combined with metformin greatly increases the risk of lactic acidosis, a rare but life-threatening condition.', advice: 'Avoid alcohol while on metformin. Discuss with your doctor before any occasion involving drinking.' },
    'refined sugar': { risk: 'MODERATE', severity: 'Moderate', effect: 'High sugar intake counteracts metformin\'s blood-glucose lowering effect.', advice: 'Follow a low-sugar, balanced diet to maximize metformin\'s effectiveness.' },
    'grapefruit': { risk: 'LOW', severity: 'Low', effect: 'Minor interaction reported; grapefruit may slightly affect metformin clearance.', advice: 'Generally safe in moderation. Monitor blood glucose levels.' },
  },
  'lisinopril': {
    'bananas': { risk: 'MODERATE', severity: 'Moderate', effect: 'Bananas are high in potassium. Lisinopril can also raise potassium levels, risking hyperkalemia.', advice: 'Limit high-potassium foods. Have potassium levels checked regularly.' },
    'salt substitute': { risk: 'HIGH', severity: 'Severe', effect: 'Salt substitutes contain potassium chloride, potentially causing dangerous potassium levels when combined with lisinopril.', advice: 'Avoid potassium-based salt substitutes entirely.' },
    'alcohol': { risk: 'MODERATE', severity: 'Moderate', effect: 'Alcohol may enhance the blood-pressure-lowering effect, causing dizziness or fainting.', advice: 'Limit alcohol intake and be cautious about rapid position changes.' },
    'grapefruit': { risk: 'LOW', severity: 'Low', effect: 'Minor CYP interaction possible but generally considered safe.', advice: 'Generally safe in normal amounts.' },
  },
  'aspirin': {
    'alcohol': { risk: 'MODERATE', severity: 'Moderate', effect: 'Alcohol combined with aspirin significantly increases risk of stomach bleeding.', advice: 'Avoid or strictly limit alcohol while taking daily aspirin.' },
    'caffeine': { risk: 'LOW', severity: 'Low', effect: 'Caffeine may slightly increase aspirin absorption speed.', advice: 'Generally safe. No action required.' },
    'ginger': { risk: 'MODERATE', severity: 'Moderate', effect: 'Both ginger and aspirin have blood-thinning effects, which may compound.', advice: 'Limit medicinal doses of ginger. Normal culinary use is typically fine.' },
  },
  'levothyroxine': {
    'coffee': { risk: 'MODERATE', severity: 'Moderate', effect: 'Coffee can reduce levothyroxine absorption by up to 36% when consumed simultaneously.', advice: 'Take levothyroxine on an empty stomach, at least 30-60 minutes before coffee or food.' },
    'soy': { risk: 'MODERATE', severity: 'Moderate', effect: 'Soy products can interfere with levothyroxine absorption.', advice: 'Take levothyroxine several hours apart from soy-containing foods.' },
    'calcium-rich foods': { risk: 'MODERATE', severity: 'Moderate', effect: 'Calcium binds to levothyroxine in the gut, reducing absorption.', advice: 'Avoid dairy and calcium-rich foods for at least 4 hours after taking levothyroxine.' },
    'walnuts': { risk: 'MODERATE', severity: 'Moderate', effect: 'Walnuts may impair levothyroxine absorption in the gut.', advice: 'Avoid eating walnuts close to taking levothyroxine.' },
  },
};

// Fuzzy match helper
function findKey(obj, query) {
  const q = query.toLowerCase().trim();
  return Object.keys(obj).find(k => q.includes(k) || k.includes(q));
}

// ──────────────────────────────────────────────
// API Methods
// ──────────────────────────────────────────────
export const authService = {
  login: async (email, password) => {
    await new Promise(r => setTimeout(r, 800));
    if (!email || !password) throw new Error('Email and password are required.');
    const mockUser = {
      id: 'usr_' + Math.random().toString(36).slice(2),
      name: email.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      email,
      age: null, gender: null, weight: null, conditions: [], allergies: [],
    };
    return { user: mockUser, token: 'mock_jwt_' + Date.now() };
  },

  signup: async (name, email, password) => {
    await new Promise(r => setTimeout(r, 1000));
    if (!name || !email || !password) throw new Error('All fields are required.');
    const mockUser = { id: 'usr_' + Math.random().toString(36).slice(2), name, email, age: null, gender: null, weight: null, conditions: [], allergies: [] };
    return { user: mockUser, token: 'mock_jwt_' + Date.now() };
  },
};

export default api;
