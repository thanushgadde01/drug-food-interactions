from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Optional ML imports are loaded lazily. If they are unavailable, the API still starts
# and falls back to mock responses for the UI's drug/food suggestions.
has_ml_backend = False
np = None
pd = None
xgb = None
Chem = None
rdMolDescriptors = None
try:
    import numpy as np
    import pandas as pd
    import xgboost as xgb
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors
    has_ml_backend = True
except Exception as exc:
    print(f"Optional ML backend unavailable: {exc}")

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
STATIC_DIR = PROJECT_ROOT / "dist"

load_dotenv(PROJECT_ROOT / ".env")

FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    if origin.strip()
]

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'app.db'}")
MODEL_PATH = Path(os.getenv("MODEL_PATH", PROJECT_ROOT / "drug_food_model.json"))
DRUG_DATASET_PATH = Path(os.getenv("DRUG_DATASET_PATH", PROJECT_ROOT / "drug_dataset.csv"))
FOOD_DATASET_PATH = Path(os.getenv("FOOD_DATASET_PATH", PROJECT_ROOT / "food_dataset.csv"))

# Always available fallback suggestions and mock interactions for the React search/suggestions UI.
FALLBACK_DRUG_SUGGESTIONS = [
    "warfarin",
    "atorvastatin",
    "metformin",
    "lisinopril",
    "aspirin",
    "levothyroxine",
    "simvastatin",
    "amlodipine",
    "omeprazole",
    "sertraline",
]

FALLBACK_FOOD_SUGGESTIONS = [
    "grapefruit",
    "alcohol",
    "spinach",
    "bananas",
    "coffee",
    "dairy",
    "soy",
    "walnuts",
    "cranberry",
    "ginger",
    "salt substitute",
    "refined sugar",
]

FALLBACK_PREDICTION_MAP: Dict[Tuple[str, str], Dict[str, str]] = {
    ("warfarin", "grapefruit"): {
        "risk": "HIGH",
        "severity": "High",
        "effect": "Grapefruit inhibits CYP3A4 and dramatically increases warfarin blood levels.",
        "advice": "Avoid grapefruit entirely while on warfarin. Contact your physician immediately if consumed.",
    },
    ("warfarin", "spinach"): {
        "risk": "MODERATE",
        "severity": "Moderate",
        "effect": "Spinach is high in vitamin K, which can counteract warfarin.",
        "advice": "Maintain a consistent vitamin K diet and monitor INR regularly.",
    },
    ("atorvastatin", "grapefruit"): {
        "risk": "HIGH",
        "severity": "High",
        "effect": "Grapefruit increases atorvastatin levels and raises muscle damage risk.",
        "advice": "Avoid grapefruit and grapefruit juice while taking atorvastatin.",
    },
    ("metformin", "alcohol"): {
        "risk": "HIGH",
        "severity": "High",
        "effect": "Alcohol increases the risk of metformin-related lactic acidosis.",
        "advice": "Avoid alcohol while on metformin and speak with your doctor before drinking.",
    },
    ("levothyroxine", "coffee"): {
        "risk": "MODERATE",
        "severity": "Moderate",
        "effect": "Coffee can reduce levothyroxine absorption when taken at the same time.",
        "advice": "Take levothyroxine on an empty stomach and wait 30-60 minutes before coffee.",
    },
    ("lisinopril", "bananas"): {
        "risk": "MODERATE",
        "severity": "Moderate",
        "effect": "Bananas are high in potassium, which can be increased by lisinopril.",
        "advice": "Limit high-potassium foods and monitor serum potassium levels.",
    },
    ("aspirin", "alcohol"): {
        "risk": "MODERATE",
        "severity": "Moderate",
        "effect": "Aspirin plus alcohol increases the risk of gastrointestinal bleeding.",
        "advice": "Avoid or strictly limit alcohol while taking aspirin.",
    },
}

FALLBACK_INTERACTIONS = [
    {
        "id": 10001,
        "drug": "Warfarin",
        "food": "Grapefruit",
        "severity": "High",
        "description": "Grapefruit juice increases warfarin blood levels.",
    },
    {
        "id": 10002,
        "drug": "Metformin",
        "food": "Alcohol",
        "severity": "High",
        "description": "Alcohol may increase the risk of lactic acidosis with metformin.",
    },
    {
        "id": 10003,
        "drug": "Levothyroxine",
        "food": "Coffee",
        "severity": "Moderate",
        "description": "Coffee can reduce levothyroxine absorption when taken together.",
    },
    {
        "id": 10004,
        "drug": "Lisinopril",
        "food": "Bananas",
        "severity": "Moderate",
        "description": "Bananas are high in potassium and may worsen lisinopril hyperkalemia risk.",
    },
]

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(
    title="Drug-Food Interaction API",
    version="1.0.0",
    description="Unified FastAPI backend for Drug-Food Interaction.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="static_assets")
else:
    print(f"Warning: frontend static directory not found: {STATIC_DIR}")


class InteractionBase(BaseModel):
    drug: str = Field(..., min_length=1)
    food: str = Field(..., min_length=1)
    severity: str = Field(..., min_length=1)
    description: Optional[str] = ""


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    drug: Optional[str]
    food: Optional[str]
    severity: Optional[str]
    description: Optional[str]


class InteractionResponse(InteractionBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class PredictionRequest(BaseModel):
    drug: str = Field(..., min_length=1)
    food: str = Field(..., min_length=1)


class PredictionResult(BaseModel):
    success: bool = True
    data: Dict[str, Any]


class HistoryCreate(BaseModel):
    drug: str = Field(..., min_length=1)
    food: str = Field(..., min_length=1)
    risk: str = Field(..., min_length=1)
    severity: str = Field(..., min_length=1)
    effect: str = Field(..., min_length=1)
    advice: str = Field(..., min_length=1)


class HistoryResponse(HistoryCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    drug = Column(String(128), nullable=False)
    food = Column(String(128), nullable=False)
    severity = Column(String(64), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class InteractionHistory(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    drug = Column(String(128), nullable=False)
    food = Column(String(128), nullable=False)
    risk = Column(String(32), nullable=False)
    severity = Column(String(32), nullable=False)
    effect = Column(Text, nullable=False)
    advice = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def normalize_name(value: str) -> str:
    return value.strip().lower()


def resolve_alias(value: str) -> str:
    alias_map = {
        "grapefruit juice": "grapefruit",
        "vitamin k": "spinach",
        "blood thinner": "warfarin",
        "statin": "atorvastatin",
        "thyroid": "levothyroxine",
    }
    normalized = normalize_name(value)
    return alias_map.get(normalized, normalized)


def load_assets() -> tuple[Optional[Any], Optional[Any], Optional[Any]]:
    if not has_ml_backend:
        print("Machine learning backend not available. Falling back to mock prediction data.")
        return None, None, None

    model_obj = None
    drug_df = None
    food_df = None

    if MODEL_PATH.exists():
        try:
            model_obj = xgb.XGBClassifier()
            model_obj.load_model(str(MODEL_PATH))
        except Exception as exc:
            print(f"Unable to load model: {exc}")
    else:
        print(f"Model file not found at {MODEL_PATH}")

    if DRUG_DATASET_PATH.exists():
        try:
            drug_df = pd.read_csv(DRUG_DATASET_PATH)
        except Exception as exc:
            print(f"Unable to load drug dataset: {exc}")
    else:
        print(f"Drug dataset not found at {DRUG_DATASET_PATH}")

    if FOOD_DATASET_PATH.exists():
        try:
            food_df = pd.read_csv(FOOD_DATASET_PATH)
        except Exception as exc:
            print(f"Unable to load food dataset: {exc}")
    else:
        print(f"Food dataset not found at {FOOD_DATASET_PATH}")

    return model_obj, drug_df, food_df


def find_best_match(df: Any, query: str, possible_columns: List[str]) -> Optional[Any]:
    query_lower = normalize_name(query)
    for column in possible_columns:
        if column not in df.columns:
            continue
        exact_match = df[df[column].astype(str).str.lower().str.strip() == query_lower]
        if not exact_match.empty:
            return exact_match.iloc[0]

    for column in possible_columns:
        if column not in df.columns:
            continue
        contains_match = df[
            df[column].astype(str).str.lower().str.contains(query_lower, na=False)
        ]
        if not contains_match.empty:
            return contains_match.iloc[0]

    return None


def lookup_smiles(
    df: Any,
    item_name: str,
    name_fields: List[str],
    smiles_fields: List[str],
) -> str:
    row = find_best_match(df, item_name, name_fields)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No match found for '{item_name}'.")
    for field in smiles_fields:
        if field in row and pd.notna(row[field]):
            return str(row[field])
    raise HTTPException(status_code=400, detail=f"No SMILES column found for '{item_name}'.")


def get_combined_features(mol: Any) -> Dict[str, float]:
    if mol is None:
        raise HTTPException(status_code=400, detail="Invalid combined SMILES string.")

    feats: Dict[str, float] = {
        "MTPSA": rdMolDescriptors.CalcTPSA(mol),
        "LabuteASA": rdMolDescriptors.CalcLabuteASA(mol),
    }
    feats.update({f"MRVSA{i}": v for i, v in enumerate(rdMolDescriptors.SMR_VSA_(mol))})
    feats.update({f"VSAEstate{i}": v for i, v in enumerate(rdMolDescriptors.CalcVSA_EState_(mol))})
    feats.update({f"EstateVSA{i}": v for i, v in enumerate(rdMolDescriptors.CalcEState_VSA_(mol))})
    feats.update({f"PEOEVSA{i}": v for i, v in enumerate(rdMolDescriptors.PEOE_VSA_(mol))})
    feats.update({f"slogPVSA{i}": v for i, v in enumerate(rdMolDescriptors.SlogP_VSA_(mol))})
    return feats


def build_feature_vector(base_feats: Dict[str, float]) -> List[float]:
    required_keys = [
        "MTPSA",
        "MRVSA0",
        "MRVSA2",
        "MRVSA8",
        "MRVSA9",
        "VSAEstate7",
        "VSAEstate10",
        "EstateVSA0",
        "EstateVSA1",
        "EstateVSA2",
        "EstateVSA7",
        "PEOEVSA5",
        "PEOEVSA9",
        "PEOEVSA10",
        "PEOEVSA12",
        "slogPVSA0",
        "slogPVSA2",
        "slogPVSA9",
    ]

    for key in required_keys:
        if key not in base_feats:
            raise HTTPException(status_code=500, detail=f"Missing descriptor feature: {key}")

    return [
        base_feats["MTPSA"] + base_feats["MTPSA"],
        base_feats["MRVSA9"],
        base_feats["MRVSA8"],
        base_feats["MRVSA0"],
        base_feats["MRVSA2"],
        base_feats["VSAEstate10"] + base_feats["VSAEstate10"],
        base_feats["EstateVSA0"] * base_feats["LabuteASA"],
        base_feats["PEOEVSA12"],
        base_feats["PEOEVSA10"],
        base_feats["PEOEVSA5"],
        base_feats["PEOEVSA9"],
        base_feats["slogPVSA2"],
        base_feats["slogPVSA0"],
        base_feats["slogPVSA9"],
        base_feats["VSAEstate7"] + base_feats["VSAEstate7"],
        base_feats["EstateVSA7"],
        base_feats["EstateVSA2"],
        base_feats["EstateVSA1"] * base_feats["VSAEstate8"],
    ]


def make_prediction_response(drug: str, food: str, prediction_data: Dict[str, str]) -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "drug": drug,
            "food": food,
            "risk": prediction_data["risk"],
            "severity": prediction_data["severity"],
            "effect": prediction_data["effect"],
            "advice": prediction_data["advice"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    }


def save_history(db: Session, entry: Dict[str, Any]) -> None:
    history = InteractionHistory(
        drug=entry["drug"],
        food=entry["food"],
        risk=entry["risk"],
        severity=entry["severity"],
        effect=entry["effect"],
        advice=entry["advice"],
    )
    db.add(history)
    db.commit()


def fallback_prediction(drug: str, food: str) -> Dict[str, Any]:
    normalized = (normalize_name(drug), normalize_name(food))
    normalized = (resolve_alias(normalized[0]), resolve_alias(normalized[1]))
    prediction_data = FALLBACK_PREDICTION_MAP.get(normalized)
    if prediction_data:
        return make_prediction_response(drug, food, prediction_data)

    if normalized[0] in FALLBACK_DRUG_SUGGESTIONS and normalized[1] in FALLBACK_FOOD_SUGGESTIONS:
        return make_prediction_response(drug, food, {
            "risk": "LOW",
            "severity": "Low",
            "effect": f"No known significant interaction was found for {drug} and {food}.",
            "advice": "This combination appears generally safe based on the fallback mock data, but always consult a healthcare provider.",
        })

    raise HTTPException(
        status_code=503,
        detail=(
            "Prediction model is unavailable and no fallback data exists for this drug/food pair. "
            "Use one of the supported compounds from the search suggestions."
        ),
    )


model, drug_df, food_df = None, None, None


@app.on_event("startup")
def startup_event() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.query(Interaction).count() == 0:
            db.add_all([
                Interaction(drug="Aspirin", food="Alcohol", severity="High", description="Can increase risk of stomach bleeding"),
                Interaction(drug="Metformin", food="Vitamin B12 Rich Foods", severity="Medium", description="May reduce B12 absorption"),
            ])
            db.commit()
    global model, drug_df, food_df
    model, drug_df, food_df = load_assets()


@app.get("/api/health")
def health_check() -> Dict[str, str]:
    return {"status": "FastAPI backend is running", "backend": "fastapi"}


@app.get("/api/interactions", response_model=List[InteractionResponse])
def list_interactions(db: Session = Depends(get_db)) -> List[InteractionResponse]:
    return db.query(Interaction).order_by(Interaction.id.desc()).all()


@app.get("/api/interactions/{interaction_id}", response_model=InteractionResponse)
def get_interaction(interaction_id: int, db: Session = Depends(get_db)) -> InteractionResponse:
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@app.post("/api/interactions", response_model=InteractionResponse, status_code=201)
def create_interaction(interaction: InteractionCreate, db: Session = Depends(get_db)) -> InteractionResponse:
    db_interaction = Interaction(**interaction.dict())
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction


@app.put("/api/interactions/{interaction_id}", response_model=InteractionResponse)
def update_interaction(interaction_id: int, interaction_update: InteractionUpdate, db: Session = Depends(get_db)) -> InteractionResponse:
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    for field, value in interaction_update.dict(exclude_unset=True).items():
        setattr(interaction, field, value)
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


@app.delete("/api/interactions/{interaction_id}", response_model=Dict[str, str])
def delete_interaction(interaction_id: int, db: Session = Depends(get_db)) -> Dict[str, str]:
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    db.delete(interaction)
    db.commit()
    return {"success": "Interaction deleted successfully"}


@app.get("/api/search", response_model=List[InteractionResponse])
def search_interactions(drug: Optional[str] = None, food: Optional[str] = None, db: Session = Depends(get_db)) -> List[InteractionResponse]:
    query = db.query(Interaction)
    if drug:
        query = query.filter(Interaction.drug.ilike(f"%{drug}%"))
    if food:
        query = query.filter(Interaction.food.ilike(f"%{food}%"))
    results = query.order_by(Interaction.id.desc()).all()

    fallback_matches = []
    if drug or food:
        requested_drug = normalize_name(drug or "")
        requested_food = normalize_name(food or "")
        for item in FALLBACK_INTERACTIONS:
            drug_match = requested_drug in normalize_name(item["drug"])
            food_match = requested_food in normalize_name(item["food"])
            if (drug and not food and drug_match) or (food and not drug and food_match) or (drug and food and drug_match and food_match):
                fallback_matches.append(InteractionResponse(**{**item, "created_at": datetime.utcnow()}))
    return results + fallback_matches


@app.get("/api/drugs")
def get_drug_suggestions() -> Dict[str, List[str]]:
    return {"drugs": [drug.title() for drug in FALLBACK_DRUG_SUGGESTIONS]}


@app.get("/api/foods")
def get_food_suggestions() -> Dict[str, List[str]]:
    return {"foods": [food.title() for food in FALLBACK_FOOD_SUGGESTIONS]}


@app.post("/api/predict", response_model=PredictionResult)
def predict_interaction(request_body: PredictionRequest, db: Session = Depends(get_db)) -> PredictionResult:
    drug = request_body.drug.strip()
    food = request_body.food.strip()
    if not drug or not food:
        raise HTTPException(status_code=400, detail="Drug and food are required.")

    if model is not None and drug_df is not None and food_df is not None:
        drug_name = resolve_alias(drug)
        food_name = resolve_alias(food)
        drug_name_fields = [col for col in ["Name", "name"] if col in drug_df.columns]
        drug_smiles_fields = [col for col in ["SMILES", "smiles"] if col in drug_df.columns]
        food_name_fields = [col for col in ["name", "Name"] if col in food_df.columns]
        food_smiles_fields = [col for col in ["moldb_smiles", "SMILES", "smiles"] if col in food_df.columns]

        if drug_name_fields and drug_smiles_fields and food_name_fields and food_smiles_fields:
            drug_smiles = lookup_smiles(drug_df, drug_name, drug_name_fields, drug_smiles_fields)
            food_smiles = lookup_smiles(food_df, food_name, food_name_fields, food_smiles_fields)
            combined_smiles = f"{drug_smiles}.{food_smiles}"
            mol = Chem.MolFromSmiles(combined_smiles)
            base_feats = get_combined_features(mol)
            feature_vector = build_feature_vector(base_feats)
            prediction_value = int(model.predict(np.array([feature_vector]))[0])

            if prediction_value == 2:
                result = {
                    "risk": "HIGH",
                    "severity": "High",
                    "effect": "High risk interaction detected! Please avoid this combination.",
                    "advice": f"Please consult your healthcare provider before combining {drug} with {food}.",
                }
            elif prediction_value == 1:
                result = {
                    "risk": "MODERATE",
                    "severity": "Medium",
                    "effect": "Moderate interaction. Proceed with caution.",
                    "advice": f"Please consult your healthcare provider before combining {drug} with {food}.",
                }
            else:
                result = {
                    "risk": "LOW",
                    "severity": "Low",
                    "effect": f"No known significant interaction was found for {drug} and {food}.",
                    "advice": "This combination appears generally safe based on current records, but always consult a healthcare provider for medical advice.",
                }
            response = make_prediction_response(drug, food, result)
            save_history(db, response["data"])
            return response

    response = fallback_prediction(drug, food)
    save_history(db, response["data"])
    return response


@app.get("/api/history", response_model=List[HistoryResponse])
def get_history(limit: int = 50, db: Session = Depends(get_db)) -> List[HistoryResponse]:
    return db.query(InteractionHistory).order_by(InteractionHistory.created_at.desc()).limit(limit).all()


@app.post("/api/history", response_model=HistoryResponse, status_code=201)
def create_history(history_data: HistoryCreate, db: Session = Depends(get_db)) -> HistoryResponse:
    history = InteractionHistory(**history_data.dict())
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


@app.get("/", include_in_schema=False)
def spa_root() -> FileResponse:
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    raise HTTPException(status_code=404, detail="Static app build not found.")


@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str) -> FileResponse:
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    raise HTTPException(status_code=404, detail="Static app build not found.")
