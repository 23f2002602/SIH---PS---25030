from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import SoilData, Farmer
from schemas import SoilDataResponse
from auth import get_current_farmer
import requests
import os
from typing import Dict, Any

router = APIRouter()

async def get_soil_data(location: str, state: str, district: str) -> Dict[str, Any]:
    """Get soil data from external API or return sample data"""
    try:
        # Try to get data from SoilGrids API (simplified)
        # In a real implementation, you would use proper API calls
        sample_soil_data = {
            'ph': 6.8,
            'nitrogen': 45.2,
            'phosphorus': 28.5,
            'potassium': 38.7,
            'organic_matter': 2.8,
            'moisture': 65.0,
            'temperature': 26.5,
            'soil_type': 'Clay Loam'
        }
        
        # You can integrate with real APIs like:
        # - SoilGrids API
        # - Bhuvan API
        # - Local soil databases
        
        return sample_soil_data
        
    except Exception as e:
        # Return default values if API fails
        return {
            'ph': 6.5,
            'nitrogen': 50.0,
            'phosphorus': 30.0,
            'potassium': 40.0,
            'organic_matter': 2.5,
            'moisture': 60.0,
            'temperature': 25.0,
            'soil_type': 'Loam'
        }

@router.post("/fetch", response_model=SoilDataResponse)
async def fetch_soil_data(
    location: str,
    state: str,
    district: str,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    """Fetch and store soil data for a location"""
    try:
        # Get soil data
        soil_data = await get_soil_data(location, state, district)
        
        # Save to database
        db_soil_data = SoilData(
            farmer_id=current_farmer.id,
            location=location,
            ph=soil_data.get('ph'),
            nitrogen=soil_data.get('nitrogen'),
            phosphorus=soil_data.get('phosphorus'),
            potassium=soil_data.get('potassium'),
            organic_matter=soil_data.get('organic_matter'),
            moisture=soil_data.get('moisture'),
            temperature=soil_data.get('temperature'),
            soil_type=soil_data.get('soil_type'),
            source='api'
        )
        
        db.add(db_soil_data)
        db.commit()
        db.refresh(db_soil_data)
        
        return db_soil_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching soil data: {str(e)}")

@router.get("/history")
async def get_soil_history(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    """Get farmer's soil data history"""
    soil_data = db.query(SoilData).filter(
        SoilData.farmer_id == current_farmer.id
    ).order_by(SoilData.created_at.desc()).all()
    
    return soil_data

