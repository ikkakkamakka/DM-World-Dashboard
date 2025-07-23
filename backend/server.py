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

# Auto-events toggle
auto_events_enabled = True

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

def generate_fantasy_event(kingdom_data):
    event_templates = [
        "{name} joins {city} as a new citizen.",
        "A child is born to the {family_name} family in {city}.",
        "{citizen} celebrates their birthday in {city}.",
        "Captain {guard} reports all is well in {city}.",
        "{merchant} opens a new shop in the market square of {city}.",
        "Elder {elder} passes away peacefully in {city}.",
        "{scholar} discovers an ancient tome in {city}.",
        "A festival begins in {city} - citizens celebrate!",
        "Heavy rains bless the crops around {city}.",
        "{guard} catches a pickpocket in {city}'s market.",
    ]
    
    event_template = random.choice(event_templates)
    cities = kingdom_data.get('cities', [])
    if not cities:
        return "The kingdom grows quiet..."
    
    city = random.choice(cities)
    city_name = city['name']
    citizens = city.get('citizens', [])
    
    if citizens:
        citizen = random.choice(citizens)
        citizen_name = citizen['name']
        
        event = event_template.format(
            name=generate_fantasy_name(),
            city=city_name,
            family_name=random.choice(FANTASY_LAST_NAMES),
            citizen=citizen_name,
            guard=f"Captain {random.choice(FANTASY_FIRST_NAMES)}",
            merchant=citizen_name,
            elder=f"Elder {generate_fantasy_name()}",
            scholar=citizen_name
        )
    else:
        event = f"A new citizen arrives in {city_name}."
    
    return event

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

class Slave(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    age: int
    origin: str  # Where they came from
    occupation: str
    owner: str
    purchase_price: int  # in gold pieces
    city_id: str
    health: str = "Healthy"
    status: str = "Enslaved"  # Enslaved, Manumitted, Dead, Escaped
    manumission_date: Optional[datetime] = None
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SlaveCreate(BaseModel):
    name: str
    age: int
    origin: str
    occupation: str
    owner: str
    purchase_price: int
    city_id: str
    health: str = "Healthy"
    notes: str = ""

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
    slaves: List[Slave] = []
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

class EventCreate(BaseModel):
    description: str
    city_name: str
    event_type: str = "manual"

# Simulation engine
async def simulation_engine():
    """Background task that generates kingdom events"""
    global auto_events_enabled
    while True:
        try:
            if auto_events_enabled:
                kingdom_data = await db.kingdoms.find_one()
                if kingdom_data:
                    event_description = generate_fantasy_event(kingdom_data)
                    
                    event = Event(
                        description=event_description,
                        city_name=random.choice(kingdom_data['cities'])['name'] if kingdom_data['cities'] else "Unknown",
                        kingdom_name=kingdom_data['name'],
                        event_type="auto"
                    )
                    
                    await db.events.insert_one(event.dict())
                    
                    await manager.broadcast({
                        "type": "new_event",
                        "event": event.dict()
                    })
            
            await asyncio.sleep(random.randint(15, 45))
            
        except Exception as e:
            logging.error(f"Simulation error: {e}")
            await asyncio.sleep(30)

# Initialize kingdom data
async def initialize_kingdom():
    """Create sample kingdom data if none exists"""
    existing_kingdom = await db.kingdoms.find_one()
    if not existing_kingdom:
        # Create sample data
        citizens_emberfalls = [
            Citizen(name="Thorin Emberthane", age=45, occupation="Blacksmith", city_id="city1"),
            Citizen(name="Elena Brightwater", age=32, occupation="Healer", city_id="city1"),
            Citizen(name="Marcus Ironforge", age=28, occupation="Guard", city_id="city1"),
        ]
        
        slaves_emberfalls = [
            Slave(name="Keth", age=25, origin="Captured Orc", occupation="Laborer", 
                  owner="City", purchase_price=50, city_id="city1"),
        ]
        
        livestock_emberfalls = [
            Livestock(name="Thunder", type="Horse", age=5, weight=1200, value=300, city_id="city1"),
            Livestock(name="Bessie", type="Cattle", age=3, weight=800, value=150, city_id="city1"),
        ]
        
        garrison_emberfalls = [
            Soldier(name="Captain Steel", rank="Captain", age=35, years_of_service=10, 
                   equipment=["Sword", "Shield", "Chain Mail"], city_id="city1"),
            Soldier(name="Corporal Brown", rank="Corporal", age=28, years_of_service=5,
                   equipment=["Crossbow", "Leather Armor"], city_id="city1"),
        ]
        
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
                slaves=slaves_emberfalls,
                livestock=livestock_emberfalls,
                garrison=garrison_emberfalls
            ),
            City(
                id="city2", 
                name="Stormhaven",
                governor="Lady Vera Stormwind",
                population=2,
                treasury=1800,
                x_coordinate=72.1,
                y_coordinate=34.5,
                citizens=[
                    Citizen(name="Gareth Stormwind", age=52, occupation="Captain", city_id="city2"),
                    Citizen(name="Aria Moonwhisper", age=29, occupation="Scholar", city_id="city2"),
                ],
                slaves=[],
                livestock=[],
                garrison=[]
            )
        ]
        
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
    task = asyncio.create_task(simulation_engine())
    yield
    # Shutdown
    task.cancel()

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

# Slaves Management
@api_router.post("/slaves")
async def create_slave(slave: SlaveCreate):
    new_slave = Slave(**slave.dict())
    
    result = await db.kingdoms.update_one(
        {"cities.id": slave.city_id},
        {"$push": {"cities.$.slaves": new_slave.dict()}}
    )
    
    if result.modified_count:
        return new_slave
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/slaves/{slave_id}")
async def delete_slave(slave_id: str):
    result = await db.kingdoms.update_one(
        {"cities.slaves.id": slave_id},
        {"$pull": {"cities.$.slaves": {"id": slave_id}}}
    )
    
    if result.modified_count:
        return {"message": "Slave deleted successfully"}
    raise HTTPException(status_code=404, detail="Slave not found")

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

@api_router.delete("/tribute/{tribute_id}")
async def delete_tribute(tribute_id: str):
    result = await db.kingdoms.update_one(
        {"cities.tribute_records.id": tribute_id},
        {"$pull": {"cities.$.tribute_records": {"id": tribute_id}}}
    )
    
    if result.modified_count:
        return {"message": "Tribute record deleted successfully"}
    raise HTTPException(status_code=404, detail="Tribute record not found")

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

@api_router.delete("/crimes/{crime_id}")
async def delete_crime(crime_id: str):
    result = await db.kingdoms.update_one(
        {"cities.crime_records.id": crime_id},
        {"$pull": {"cities.$.crime_records": {"id": crime_id}}}
    )
    
    if result.modified_count:
        return {"message": "Crime record deleted successfully"}
    raise HTTPException(status_code=404, detail="Crime record not found")

# Events Management
@api_router.get("/events")
async def get_recent_events(limit: int = 20):
    events = await db.events.find().sort("timestamp", -1).limit(limit).to_list(limit)
    for event in events:
        event.pop('_id', None)
    return events

@api_router.post("/events")
async def create_manual_event(event: EventCreate):
    kingdom = await db.kingdoms.find_one()
    kingdom_name = kingdom['name'] if kingdom else "Unknown Kingdom"
    
    new_event = Event(
        description=event.description,
        city_name=event.city_name,
        kingdom_name=kingdom_name,
        event_type="manual"
    )
    
    await db.events.insert_one(new_event.dict())
    
    await manager.broadcast({
        "type": "new_event",
        "event": new_event.dict()
    })
    
    return new_event

@api_router.post("/toggle-auto-events")
async def toggle_auto_events():
    global auto_events_enabled
    auto_events_enabled = not auto_events_enabled
    return {"auto_events_enabled": auto_events_enabled}

@api_router.get("/auto-events-status")
async def get_auto_events_status():
    return {"auto_events_enabled": auto_events_enabled}

@api_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
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