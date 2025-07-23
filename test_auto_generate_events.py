#!/usr/bin/env python3
"""
Test that auto-generate creates proper events
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading backend URL: {e}")
        return None

BACKEND_URL = get_backend_url()
API_BASE = f"{BACKEND_URL}/api"

async def test_auto_generate_events():
    """Test that auto-generate creates events"""
    async with aiohttp.ClientSession() as session:
        # Get initial event count
        async with session.get(f"{API_BASE}/events?limit=5") as response:
            if response.status != 200:
                print("❌ Failed to get events")
                return
            
            initial_events = await response.json()
            initial_count = len(initial_events)
            
            print(f"📜 Initial event count: {initial_count}")
            
            # Get a city to test with
            async with session.get(f"{API_BASE}/kingdom") as kingdom_response:
                kingdom_data = await kingdom_response.json()
                test_city = kingdom_data['cities'][0]
                city_id = test_city['id']
                city_name = test_city['name']
                
                print(f"🏘️ Testing with city: {city_name}")
                
                # Generate a citizen
                payload = {
                    "registry_type": "citizens",
                    "city_id": city_id,
                    "count": 1
                }
                
                async with session.post(f"{API_BASE}/auto-generate", json=payload) as gen_response:
                    if gen_response.status == 200:
                        result = await gen_response.json()
                        generated_item = result['generated_items'][0]
                        print(f"✅ Generated citizen: {generated_item['name']} ({generated_item['occupation']})")
                        
                        # Wait a moment for event to be created
                        await asyncio.sleep(2)
                        
                        # Check for new events
                        async with session.get(f"{API_BASE}/events?limit=10") as events_response:
                            new_events = await events_response.json()
                            
                            # Look for recent events related to our generation
                            current_time = datetime.utcnow()
                            
                            for event in new_events:
                                event_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                                time_diff = (current_time - event_time.replace(tzinfo=None)).total_seconds()
                                
                                if time_diff <= 10:  # Within last 10 seconds
                                    description = event['description']
                                    if generated_item['name'] in description and city_name in description:
                                        print(f"✅ Found matching event: {description}")
                                        print(f"   Event type: {event.get('event_type', 'unknown')}")
                                        print(f"   City: {event['city_name']}")
                                        return
                            
                            print("⚠️ No matching event found for generated citizen")
                    else:
                        print("❌ Failed to generate citizen")

if __name__ == "__main__":
    asyncio.run(test_auto_generate_events())