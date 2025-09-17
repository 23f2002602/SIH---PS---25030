from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Farmer, CropRecommendation
from schemas import CropRecommendationRequest, CropRecommendationResponse
from auth import get_current_farmer
from services.ml_service import MLService
from routers.soil import get_soil_data
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

router = APIRouter()
ml_service = MLService()

# Minimal weather data provider to replace missing routers.weather module
async def get_weather_data(location: str, state: str, district: str) -> Dict[str, Any]:
    try:
        # Return sample weather data; replace with real API integration as needed
        return {
            'temperature': 26.0,
            'humidity': 70.0,
            'rainfall': 950.0,
            'wind_speed': 8.5,
            'pressure': 1012.0,
            'weather_condition': 'Partly Cloudy'
        }
    except Exception:
        return {
            'temperature': 25.0,
            'humidity': 65.0,
            'rainfall': 800.0,
            'wind_speed': 6.0,
            'pressure': 1010.0,
            'weather_condition': 'Clear'
        }

@router.post("/crops", response_model=List[CropRecommendationResponse])
async def get_crop_recommendations(
    request: CropRecommendationRequest,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    """Get crop recommendations based on location, soil, and weather data"""
    try:
        # Get soil data for the location
        soil_data = await get_soil_data(request.location, request.state, request.district)
        
        # Get weather data for the location
        weather_data = await get_weather_data(request.location, request.state, request.district)
        
        # Get recommendations from ML service
        recommendations = ml_service.get_crop_recommendations(
            soil_data, weather_data, request.season, request.state
        )
        
        # Save recommendations to database
        for rec in recommendations:
            db_recommendation = CropRecommendation(
                farmer_id=current_farmer.id,
                crop_name=rec['crop_name'],
                confidence_score=rec['confidence_score'],
                expected_yield=rec['expected_yield'],
                expected_profit=rec['expected_profit'],
                sustainability_score=rec['sustainability_score'],
                fertilizer_recommendation=json.dumps(rec['fertilizer_recommendation']),
                planting_date=datetime.now() + timedelta(days=7),
                harvesting_date=datetime.now() + timedelta(days=120)
            )
            db.add(db_recommendation)
        
        db.commit()
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

@router.get("/history")
async def get_recommendation_history(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    """Get farmer's recommendation history"""
    recommendations = db.query(CropRecommendation).filter(
        CropRecommendation.farmer_id == current_farmer.id
    ).order_by(CropRecommendation.created_at.desc()).all()
    
    return recommendations

