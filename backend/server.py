from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks
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
    "Petra", "Quentin", "Raven", "Senna", "Thane", "Ulric", "Vera", "Willem", "Xara", "Yorick", "Zara",
    "Aldric", "Brenna", "Cedric", "Delia", "Eamon", "Faye", "Gideon", "Hera", "Ian", "Jora"
]

FANTASY_LAST_NAMES = [
    "Stormwind", "Ironforge", "Goldleaf", "Shadowmere", "Brightblade", "Darkwood", 
    "Silvermoon", "Redstone", "Blackwater", "Whitehawk", "Greycloak", "Bluethorn",
    "Emberthane", "Frostborn", "Sunblade", "Moonwhisper", "Starweaver", "Flamekeeper",
    "Stormcaller", "Earthshaker", "Windrider", "Lightbringer", "Shadowbane", "Dragonheart"
]

CITY_NAMES = [
    "Emberfalls", "Stormhaven", "Silverbrook", "Ironwatch", "Goldenvale", 
    "Shadowmere", "Brightwater", "Darkwood", "Crystalspire", "Moonhaven"
]

OCCUPATIONS = [
    "Blacksmith", "Baker", "Merchant", "Guard", "Scholar", "Healer", "Farmer", 
    "Carpenter", "Mason", "Innkeeper", "Scribe", "Mage", "Archer", "Knight"
]

FANTASY_EVENTS = [
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
    "A traveling bard performs in {city}'s tavern.",
    "{citizen} is promoted to guild leader in {city}."
]

def generate_fantasy_name():
    return f"{random.choice(FANTASY_FIRST_NAMES)} {random.choice(FANTASY_LAST_NAMES)}"

def generate_fantasy_event(kingdom_data):
    event_template = random.choice(FANTASY_EVENTS)
    
    # Get random city
    cities = kingdom_data.get('cities', [])
    if not cities:
        return "The kingdom grows quiet..."
    
    city = random.choice(cities)
    city_name = city['name']
    
    # Get random citizen from that city
    citizens = city.get('citizens', [])
    
    if citizens:
        citizen = random.choice(citizens)
        citizen_name = citizen['name']
        
        # Replace placeholders
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

# Data Models
class Citizen(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    age: int
    occupation: str
    city_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class City(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    governor: str
    population: int = 0
    treasury: int = 1000
    citizens: List[Citizen] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

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

# Simulation engine
async def simulation_engine():
    """Background task that generates kingdom events"""
    while True:
        try:
            # Get kingdom data
            kingdom_data = await db.kingdoms.find_one()
            if kingdom_data:
                # Generate random event
                event_description = generate_fantasy_event(kingdom_data)
                
                # Create event
                event = Event(
                    description=event_description,
                    city_name=random.choice(kingdom_data['cities'])['name'] if kingdom_data['cities'] else "Unknown",
                    kingdom_name=kingdom_data['name']
                )
                
                # Save to database
                await db.events.insert_one(event.dict())
                
                # Broadcast to connected clients
                await manager.broadcast({
                    "type": "new_event",
                    "event": event.dict()
                })
                
                # Randomly update population or treasury
                if random.random() < 0.3:  # 30% chance
                    if random.choice([True, False]):
                        # Add citizen to random city
                        city_to_update = random.choice(kingdom_data['cities'])
                        new_citizen = Citizen(
                            name=generate_fantasy_name(),
                            age=random.randint(18, 60),
                            occupation=random.choice(OCCUPATIONS),
                            city_id=city_to_update['id']
                        )
                        
                        # Update city in database
                        await db.kingdoms.update_one(
                            {"cities.id": city_to_update['id']},
                            {
                                "$push": {"cities.$.citizens": new_citizen.dict()},
                                "$inc": {"cities.$.population": 1, "total_population": 1}
                            }
                        )
            
            # Wait before next event (10-30 seconds for demo purposes)
            await asyncio.sleep(random.randint(10, 30))
            
        except Exception as e:
            logging.error(f"Simulation error: {e}")
            await asyncio.sleep(30)

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
            Citizen(name="Lydia Goldleaf", age=39, occupation="Merchant", city_id="city1"),
        ]
        
        citizens_stormhaven = [
            Citizen(name="Gareth Stormwind", age=52, occupation="Captain", city_id="city2"),
            Citizen(name="Aria Moonwhisper", age=29, occupation="Scholar", city_id="city2"),
            Citizen(name="Bram Darkwood", age=41, occupation="Baker", city_id="city2"),
        ]
        
        # Create sample cities
        cities = [
            City(
                id="city1",
                name="Emberfalls",
                governor="Lord Aldric Emberthane",
                population=len(citizens_emberfalls),
                treasury=2500,
                citizens=citizens_emberfalls
            ),
            City(
                id="city2", 
                name="Stormhaven",
                governor="Lady Vera Stormwind",
                population=len(citizens_stormhaven),
                treasury=1800,
                citizens=citizens_stormhaven
            )
        ]
        
        # Create kingdom
        kingdom = Kingdom(
            name="Cartborne Kingdom",
            ruler="King Darius the Wise",
            total_population=sum(city.population for city in cities),
            royal_treasury=5000,
            cities=cities
        )
        
        await db.kingdoms.insert_one(kingdom.dict())
        logging.info("Sample kingdom data initialized")

# Background task startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await initialize_kingdom()
    task = asyncio.create_task(simulation_engine())
    yield
    # Shutdown
    task.cancel()

# Create the main app
app = FastAPI(lifespan=lifespan)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# API Routes
@api_router.get("/kingdom")
async def get_kingdom():
    kingdom = await db.kingdoms.find_one()
    if kingdom:
        # Remove MongoDB _id field
        kingdom.pop('_id', None)
        return kingdom
    return {"error": "Kingdom not found"}

@api_router.get("/city/{city_id}")
async def get_city(city_id: str):
    kingdom = await db.kingdoms.find_one()
    if kingdom:
        for city in kingdom['cities']:
            if city['id'] == city_id:
                return city
    return {"error": "City not found"}

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