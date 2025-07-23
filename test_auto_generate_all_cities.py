#!/usr/bin/env python3
"""
Test auto-generate functionality across all cities
"""

import asyncio
import aiohttp
import json

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

async def test_auto_generate_all_cities():
    """Test auto-generate functionality for all cities"""
    async with aiohttp.ClientSession() as session:
        # Get all cities
        async with session.get(f"{API_BASE}/kingdom") as response:
            if response.status != 200:
                print("❌ Failed to get kingdom data")
                return
            
            kingdom_data = await response.json()
            cities = kingdom_data.get('cities', [])
            
            print(f"🏰 Testing auto-generate across {len(cities)} cities")
            
            for city in cities:
                city_id = city['id']
                city_name = city['name']
                
                print(f"\n🏘️ Testing city: {city_name} (ID: {city_id})")
                
                # Test each registry type for this city
                registry_types = ["citizens", "slaves", "livestock", "garrison", "crimes", "tribute"]
                
                for registry_type in registry_types:
                    payload = {
                        "registry_type": registry_type,
                        "city_id": city_id,
                        "count": 1
                    }
                    
                    async with session.post(f"{API_BASE}/auto-generate", json=payload) as gen_response:
                        if gen_response.status == 200:
                            result = await gen_response.json()
                            generated_count = result.get('count', 0)
                            print(f"   ✅ {registry_type}: Generated {generated_count} item(s)")
                        else:
                            error_text = await gen_response.text()
                            print(f"   ❌ {registry_type}: Failed - {error_text}")

if __name__ == "__main__":
    asyncio.run(test_auto_generate_all_cities())