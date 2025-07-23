from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
import logging
import json
import random
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

manager = ConnectionManager()

# Fantasy name generators
FANTASY_FIRST_NAMES = [
    "Aelindra", "Brak", "Caelynn", "Darius", "Eryndor", "Faelyn", "Gareth", 
    "Hilda", "Ivara", "Jareth", "Kira", "Lyra", "Magnus", "Nora", "Orin",
    "Petra", "Quentin", "Raven", "Senna", "Thane", "Ulric", "Vera", "Willem", "Xara", "Yorick", "Zara"
]

FANTASY_LAST_NAMES = [
    "Stormwind", "Ironforge", "Goldleaf", "Shadowmere", "Brightblade", "Darkwood", 
    "Silvermoon", "Redstone", "Blackwater", "Whitehawk", "Greycloak", "Bluethorn"
]

OCCUPATIONS = [
    "Blacksmith", "Baker", "Merchant", "Guard", "Scholar", "Healer", "Farmer", 
    "Carpenter", "Mason", "Innkeeper", "Scribe", "Mage", "Archer", "Knight"
]

LIVESTOCK_TYPES = [
    "Cattle", "Horse", "Goat", "Sheep", "Chicken", "Pig", "Ox", "Mule", "Donkey"
]

MILITARY_RANKS = [
    "Recruit", "Private", "Corporal", "Sergeant", "Lieutenant", "Captain", "Major", "Commander"
]

CRIME_TYPES = [
    "Theft", "Assault", "Murder", "Fraud", "Smuggling", "Vandalism", "Disturbing Peace", "Tax Evasion"
]

def generate_fantasy_name():
    return f"{random.choice(FANTASY_FIRST_NAMES)} {random.choice(FANTASY_LAST_NAMES)}"

# Extended Data Models
class Citizen(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    age: int
    occupation: str
    city_id: str
    health: str = "Healthy"
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CitizenCreate(BaseModel):
    name: str
    age: int
    occupation: str
    city_id: str
    health: str = "Healthy"
    notes: str = ""

class CitizenUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    occupation: Optional[str] = None
    health: Optional[str] = None
    notes: Optional[str] = None

class Livestock(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # Cattle, Horse, etc.
    age: int
    health: str = "Healthy"
    weight: int  # in pounds
    value: int  # in gold pieces
    city_id: str
    owner: str = "City"
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LivestockCreate(BaseModel):
    name: str
    type: str
    age: int
    health: str = "Healthy"
    weight: int
    value: int
    city_id: str
    owner: str = "City"
    notes: str = ""

class Soldier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    rank: str
    age: int
    years_of_service: int
    equipment: List[str] = []
    status: str = "Active"  # Active, Injured, Deserter, Dead
    city_id: str
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SoldierCreate(BaseModel):
    name: str
    rank: str
    age: int
    years_of_service: int = 0
    equipment: List[str] = []
    status: str = "Active"
    city_id: str
    notes: str = ""

class TributeRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_city: str
    to_city: str
    amount: int  # in gold pieces
    type: str = "Gold"  # Gold, Goods, Services
    purpose: str
    status: str = "Pending"  # Pending, Paid, Overdue
    due_date: datetime
    paid_date: Optional[datetime] = None
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TributeCreate(BaseModel):
    from_city: str
    to_city: str
    amount: int
    type: str = "Gold"
    purpose: str
    due_date: datetime
    notes: str = ""

class CrimeRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    criminal_name: str
    crime_type: str
    description: str
    city_id: str
    punishment: str = ""
    status: str = "Reported"  # Reported, Investigated, Resolved
    fine_amount: int = 0
    date_occurred: datetime
    date_resolved: Optional[datetime] = None
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CrimeCreate(BaseModel):
    criminal_name: str
    crime_type: str
    description: str
    city_id: str
    punishment: str = ""
    fine_amount: int = 0
    date_occurred: datetime
    notes: str = ""

class City(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    governor: str
    population: int = 0
    treasury: int = 1000
    x_coordinate: float = 0.0  # Map coordinates
    y_coordinate: float = 0.0
    citizens: List[Citizen] = []
    livestock: List[Livestock] = []
    garrison: List[Soldier] = []
    tribute_records: List[TributeRecord] = []
    crime_records: List[CrimeRecord] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CityCreate(BaseModel):
    name: str
    governor: str
    x_coordinate: float = 0.0
    y_coordinate: float = 0.0

class CityUpdate(BaseModel):
    name: Optional[str] = None
    governor: Optional[str] = None
    treasury: Optional[int] = None
    x_coordinate: Optional[float] = None
    y_coordinate: Optional[float] = None

class Kingdom(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    ruler: str
    total_population: int = 0
    royal_treasury: int = 5000
    cities: List[City] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    city_name: str
    kingdom_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str = "general"

# Initialize kingdom data
async def initialize_kingdom():
    """Create sample kingdom data if none exists"""
    existing_kingdom = await db.kingdoms.find_one()
    if not existing_kingdom:
        # Create sample citizens
        citizens_emberfalls = [
            Citizen(name="Thorin Emberthane", age=45, occupation="Blacksmith", city_id="city1"),
            Citizen(name="Elena Brightwater", age=32, occupation="Healer", city_id="city1"),
            Citizen(name="Marcus Ironforge", age=28, occupation="Guard", city_id="city1"),
        ]
        
        citizens_stormhaven = [
            Citizen(name="Gareth Stormwind", age=52, occupation="Captain", city_id="city2"),
            Citizen(name="Aria Moonwhisper", age=29, occupation="Scholar", city_id="city2"),
        ]
        
        # Create sample livestock
        livestock_emberfalls = [
            Livestock(name="Thunder", type="Horse", age=5, weight=1200, value=300, city_id="city1"),
            Livestock(name="Bessie", type="Cattle", age=3, weight=800, value=150, city_id="city1"),
        ]
        
        # Create sample soldiers
        garrison_emberfalls = [
            Soldier(name="Captain Steel", rank="Captain", age=35, years_of_service=10, 
                   equipment=["Sword", "Shield", "Chain Mail"], city_id="city1"),
            Soldier(name="Corporal Brown", rank="Corporal", age=28, years_of_service=5,
                   equipment=["Crossbow", "Leather Armor"], city_id="city1"),
        ]
        
        # Create sample cities with coordinates
        cities = [
            City(
                id="city1",
                name="Emberfalls",
                governor="Lord Aldric Emberthane",
                population=len(citizens_emberfalls),
                treasury=2500,
                x_coordinate=45.2,
                y_coordinate=67.8,
                citizens=citizens_emberfalls,
                livestock=livestock_emberfalls,
                garrison=garrison_emberfalls
            ),
            City(
                id="city2", 
                name="Stormhaven",
                governor="Lady Vera Stormwind",
                population=len(citizens_stormhaven),
                treasury=1800,
                x_coordinate=72.1,
                y_coordinate=34.5,
                citizens=citizens_stormhaven,
                livestock=[],
                garrison=[]
            )
        ]
        
        # Create kingdom
        kingdom = Kingdom(
            name="Faerûn Campaign",
            ruler="Dungeon Master",
            total_population=sum(city.population for city in cities),
            royal_treasury=5000,
            cities=cities
        )
        
        await db.kingdoms.insert_one(kingdom.dict())
        logging.info("Sample kingdom data initialized")

# Create the main app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await initialize_kingdom()
    yield
    # Shutdown
    pass

app = FastAPI(lifespan=lifespan)
api_router = APIRouter(prefix="/api")

# Kingdom & City Management
@api_router.get("/kingdom")
async def get_kingdom():
    kingdom = await db.kingdoms.find_one()
    if kingdom:
        kingdom.pop('_id', None)
        return kingdom
    return {"error": "Kingdom not found"}

@api_router.put("/kingdom")
async def update_kingdom(name: str, ruler: str):
    result = await db.kingdoms.update_one(
        {},
        {"$set": {"name": name, "ruler": ruler}}
    )
    if result.modified_count:
        return {"message": "Kingdom updated successfully"}
    raise HTTPException(status_code=404, detail="Kingdom not found")

@api_router.post("/cities")
async def create_city(city: CityCreate):
    new_city = City(**city.dict())
    
    result = await db.kingdoms.update_one(
        {},
        {"$push": {"cities": new_city.dict()}}
    )
    
    if result.modified_count:
        await manager.broadcast({
            "type": "city_created",
            "city": new_city.dict()
        })
        return new_city
    raise HTTPException(status_code=404, detail="Kingdom not found")

@api_router.get("/city/{city_id}")
async def get_city(city_id: str):
    kingdom = await db.kingdoms.find_one()
    if kingdom:
        for city in kingdom['cities']:
            if city['id'] == city_id:
                return city
    raise HTTPException(status_code=404, detail="City not found")

@api_router.put("/city/{city_id}")
async def update_city(city_id: str, updates: CityUpdate):
    update_data = {f"cities.$.{k}": v for k, v in updates.dict(exclude_unset=True).items()}
    
    result = await db.kingdoms.update_one(
        {"cities.id": city_id},
        {"$set": update_data}
    )
    
    if result.modified_count:
        return {"message": "City updated successfully"}
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/city/{city_id}")
async def delete_city(city_id: str):
    result = await db.kingdoms.update_one(
        {},
        {"$pull": {"cities": {"id": city_id}}}
    )
    
    if result.modified_count:
        await manager.broadcast({
            "type": "city_deleted",
            "city_id": city_id
        })
        return {"message": "City deleted successfully"}
    raise HTTPException(status_code=404, detail="City not found")

# Citizens Management
@api_router.post("/citizens")
async def create_citizen(citizen: CitizenCreate):
    new_citizen = Citizen(**citizen.dict())
    
    result = await db.kingdoms.update_one(
        {"cities.id": citizen.city_id},
        {
            "$push": {"cities.$.citizens": new_citizen.dict()},
            "$inc": {"cities.$.population": 1, "total_population": 1}
        }
    )
    
    if result.modified_count:
        await manager.broadcast({
            "type": "citizen_added",
            "citizen": new_citizen.dict()
        })
        return new_citizen
    raise HTTPException(status_code=404, detail="City not found")

@api_router.put("/citizens/{citizen_id}")
async def update_citizen(citizen_id: str, updates: CitizenUpdate):
    update_data = {f"cities.$[].citizens.$.{k}": v for k, v in updates.dict(exclude_unset=True).items()}
    
    result = await db.kingdoms.update_one(
        {"cities.citizens.id": citizen_id},
        {"$set": update_data}
    )
    
    if result.modified_count:
        return {"message": "Citizen updated successfully"}
    raise HTTPException(status_code=404, detail="Citizen not found")

@api_router.delete("/citizens/{citizen_id}")
async def delete_citizen(citizen_id: str):
    result = await db.kingdoms.update_one(
        {"cities.citizens.id": citizen_id},
        {
            "$pull": {"cities.$.citizens": {"id": citizen_id}},
            "$inc": {"cities.$.population": -1, "total_population": -1}
        }
    )
    
    if result.modified_count:
        return {"message": "Citizen deleted successfully"}
    raise HTTPException(status_code=404, detail="Citizen not found")

# Livestock Management
@api_router.post("/livestock")
async def create_livestock(livestock: LivestockCreate):
    new_livestock = Livestock(**livestock.dict())
    
    result = await db.kingdoms.update_one(
        {"cities.id": livestock.city_id},
        {"$push": {"cities.$.livestock": new_livestock.dict()}}
    )
    
    if result.modified_count:
        return new_livestock
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/livestock/{livestock_id}")
async def delete_livestock(livestock_id: str):
    result = await db.kingdoms.update_one(
        {"cities.livestock.id": livestock_id},
        {"$pull": {"cities.$.livestock": {"id": livestock_id}}}
    )
    
    if result.modified_count:
        return {"message": "Livestock deleted successfully"}
    raise HTTPException(status_code=404, detail="Livestock not found")

# Military/Garrison Management
@api_router.post("/soldiers")
async def create_soldier(soldier: SoldierCreate):
    new_soldier = Soldier(**soldier.dict())
    
    result = await db.kingdoms.update_one(
        {"cities.id": soldier.city_id},
        {"$push": {"cities.$.garrison": new_soldier.dict()}}
    )
    
    if result.modified_count:
        return new_soldier
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/soldiers/{soldier_id}")
async def delete_soldier(soldier_id: str):
    result = await db.kingdoms.update_one(
        {"cities.garrison.id": soldier_id},
        {"$pull": {"cities.$.garrison": {"id": soldier_id}}}
    )
    
    if result.modified_count:
        return {"message": "Soldier deleted successfully"}
    raise HTTPException(status_code=404, detail="Soldier not found")

# Tribute Management
@api_router.post("/tribute")
async def create_tribute(tribute: TributeCreate):
    new_tribute = TributeRecord(**tribute.dict())
    
    result = await db.kingdoms.update_one(
        {"cities.name": tribute.from_city},
        {"$push": {"cities.$.tribute_records": new_tribute.dict()}}
    )
    
    if result.modified_count:
        return new_tribute
    raise HTTPException(status_code=404, detail="City not found")

# Crime Management
@api_router.post("/crimes")
async def create_crime(crime: CrimeCreate):
    new_crime = CrimeRecord(**crime.dict())
    
    result = await db.kingdoms.update_one(
        {"cities.id": crime.city_id},
        {"$push": {"cities.$.crime_records": new_crime.dict()}}
    )
    
    if result.modified_count:
        return new_crime
    raise HTTPException(status_code=404, detail="City not found")

# Events and WebSocket
@api_router.get("/events")
async def get_recent_events(limit: int = 20):
    events = await db.events.find().sort("timestamp", -1).limit(limit).to_list(limit)
    for event in events:
        event.pop('_id', None)
    return events

@api_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()