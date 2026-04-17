"""Company and user definitions for all 10 golden projects.

Each golden project has one company and one primary user.
IDs are stable (deterministic) so MERGE can match on re-runs.
"""

from backend.fixtures.golden.helpers import now_iso

# -----------------------------------------------------------------------
# GP01 — Solo Handyman, Kitchen Reno (US — Florida)
# -----------------------------------------------------------------------
GP01_COMPANY = {
    "id": "comp_gp01",
    "name": "Mike's Handyman Services",
    "address": "2847 Palm Beach Blvd, Fort Myers, FL 33916",
    "license_number": "FL-CBC1265432",
    "trade_type": "general",
    "owner_name": "Mike Torres",
    "phone": "239-555-0147",
    "email": "mike@mikeshandyman.com",
    "jurisdiction_code": "US",
    "subscription_status": "active",
    "subscription_plan": "Starter",
    "created_at": now_iso(),
    "updated_at": now_iso(),
    "created_by": "user_gp01_mike",
    "actor_type": "human",
    "updated_by": "user_gp01_mike",
    "updated_actor_type": "human",
    "agent_id": None,
    "model_id": None,
    "confidence": None,
}

GP01_USER = {
    "uid": "user_gp01_mike",
    "email": "mike@mikeshandyman.com",
    "name": "Mike Torres",
    "role": "owner",
    "company_id": "comp_gp01",
}

# -----------------------------------------------------------------------
# GP02 — Residential Extension, Deck Build (CA — Ontario)
# -----------------------------------------------------------------------
GP02_COMPANY = {
    "id": "comp_gp02",
    "name": "Lakeshore Builders Inc.",
    "address": "115 King Street W, Toronto, ON M5H 1J8",
    "license_number": "ON-RBQ-78234",
    "trade_type": "general",
    "owner_name": "Sarah Chen",
    "phone": "416-555-0233",
    "email": "sarah@lakeshorebuilders.ca",
    "jurisdiction_code": "CA",
    "subscription_status": "active",
    "subscription_plan": "Starter",
    "created_at": now_iso(),
    "updated_at": now_iso(),
    "created_by": "user_gp02_sarah",
    "actor_type": "human",
    "updated_by": "user_gp02_sarah",
    "updated_actor_type": "human",
    "agent_id": None,
    "model_id": None,
    "confidence": None,
}

GP02_USER = {
    "uid": "user_gp02_sarah",
    "email": "sarah@lakeshorebuilders.ca",
    "name": "Sarah Chen",
    "role": "owner",
    "company_id": "comp_gp02",
}

# -----------------------------------------------------------------------
# GP03 — Shop Fitout, Retail (UK — England)
# -----------------------------------------------------------------------
GP03_COMPANY = {
    "id": "comp_gp03",
    "name": "Brightstone Interiors Ltd",
    "address": "42 Commercial Road, London E1 1LP",
    "license_number": "UK-CHAS-90124",
    "trade_type": "general",
    "owner_name": "James Okafor",
    "phone": "+44-20-7946-0321",
    "email": "james@brightstone.co.uk",
    "jurisdiction_code": "UK",
    "subscription_status": "active",
    "subscription_plan": "Starter",
    "created_at": now_iso(),
    "updated_at": now_iso(),
    "created_by": "user_gp03_james",
    "actor_type": "human",
    "updated_by": "user_gp03_james",
    "updated_actor_type": "human",
    "agent_id": None,
    "model_id": None,
    "confidence": None,
}

GP03_USER = {
    "uid": "user_gp03_james",
    "email": "james@brightstone.co.uk",
    "name": "James Okafor",
    "role": "owner",
    "company_id": "comp_gp03",
}

# -----------------------------------------------------------------------
# GP04 — Custom Home Build (US — California)
# -----------------------------------------------------------------------
GP04_COMPANY = {
    "id": "comp_gp04",
    "name": "Pacific Coast Construction",
    "address": "1820 El Camino Real, San Mateo, CA 94402",
    "license_number": "CA-CSLB-1045678",
    "trade_type": "general",
    "owner_name": "David Nguyen",
    "phone": "650-555-0489",
    "email": "david@pacificcoastconstruction.com",
    "jurisdiction_code": "US",
    "subscription_status": "active",
    "subscription_plan": "Professional",
    "created_at": now_iso(),
    "updated_at": now_iso(),
    # demo_user_001 so the demo mode login can access this company
    "created_by": "demo_user_001",
    "actor_type": "human",
    "updated_by": "user_gp04_david",
    "updated_actor_type": "human",
    "agent_id": None,
    "model_id": None,
    "confidence": None,
}

GP04_USER = {
    "uid": "demo_user_001",
    "email": "demo@kerf.build",
    "name": "David Nguyen",
    "role": "owner",
    "company_id": "comp_gp04",
}

# -----------------------------------------------------------------------
# GP05 — Warehouse Fitout (AU — New South Wales)
# -----------------------------------------------------------------------
GP05_COMPANY = {
    "id": "comp_gp05",
    "name": "Southern Cross Industrial Pty Ltd",
    "address": "28 Parramatta Road, Homebush, NSW 2140",
    "license_number": "AU-NSW-BC-267845",
    "trade_type": "general",
    "owner_name": "Emma Walsh",
    "phone": "+61-2-9746-5521",
    "email": "emma@southerncrossindustrial.com.au",
    "jurisdiction_code": "AU",
    "subscription_status": "active",
    "subscription_plan": "Professional",
    "created_at": now_iso(),
    "updated_at": now_iso(),
    "created_by": "user_gp05_emma",
    "actor_type": "human",
    "updated_by": "user_gp05_emma",
    "updated_actor_type": "human",
    "agent_id": None,
    "model_id": None,
    "confidence": None,
}

GP05_USER = {
    "uid": "user_gp05_emma",
    "email": "emma@southerncrossindustrial.com.au",
    "name": "Emma Walsh",
    "role": "owner",
    "company_id": "comp_gp05",
}

# -----------------------------------------------------------------------
# GP06 — School Renovation, Mid-Project (CA — British Columbia)
# -----------------------------------------------------------------------
GP06_COMPANY = {
    "id": "comp_gp06",
    "name": "Fraser Valley Contracting Ltd",
    "address": "3400 Douglas Street, Victoria, BC V8Z 3L2",
    "license_number": "CA-BC-LIC-45892",
    "trade_type": "general",
    "owner_name": "Ryan Patel",
    "phone": "250-555-0178",
    "email": "ryan@fraservalleycontracting.ca",
    "jurisdiction_code": "CA",
    "subscription_status": "active",
    "subscription_plan": "Professional",
    "created_at": now_iso(),
    "updated_at": now_iso(),
    "created_by": "user_gp06_ryan",
    "actor_type": "human",
    "updated_by": "user_gp06_ryan",
    "updated_actor_type": "human",
    "agent_id": None,
    "model_id": None,
    "confidence": None,
}

GP06_USER = {
    "uid": "user_gp06_ryan",
    "email": "ryan@fraservalleycontracting.ca",
    "name": "Ryan Patel",
    "role": "owner",
    "company_id": "comp_gp06",
}

# -----------------------------------------------------------------------
# GP07 — Commercial High-Rise Phase 2 (US — New York)
# -----------------------------------------------------------------------
GP07_COMPANY = {
    "id": "comp_gp07",
    "name": "Manhattan Skyline Builders LLC",
    "address": "350 Fifth Avenue, Suite 4200, New York, NY 10118",
    "license_number": "NY-DOB-ALT-2024-9876",
    "trade_type": "general",
    "owner_name": "Anthony Russo",
    "phone": "212-555-0634",
    "email": "arusso@manhattanskyline.com",
    "jurisdiction_code": "US",
    "subscription_status": "active",
    "subscription_plan": "Business",
    "created_at": now_iso(),
    "updated_at": now_iso(),
    "created_by": "user_gp07_anthony",
    "actor_type": "human",
    "updated_by": "user_gp07_anthony",
    "updated_actor_type": "human",
    "agent_id": None,
    "model_id": None,
    "confidence": None,
}

GP07_USER = {
    "uid": "user_gp07_anthony",
    "email": "arusso@manhattanskyline.com",
    "name": "Anthony Russo",
    "role": "owner",
    "company_id": "comp_gp07",
}

# -----------------------------------------------------------------------
# GP08 — Highway Bridge Replacement (US — Texas)
# -----------------------------------------------------------------------
GP08_COMPANY = {
    "id": "comp_gp08",
    "name": "Lone Star Infrastructure Corp",
    "address": "4500 S. Congress Ave, Austin, TX 78745",
    "license_number": "TX-TDLR-GC-88432",
    "trade_type": "general",
    "owner_name": "Maria Gonzalez",
    "phone": "512-555-0891",
    "email": "mgonzalez@lonestarinfra.com",
    "jurisdiction_code": "US",
    "subscription_status": "active",
    "subscription_plan": "Business",
    "created_at": now_iso(),
    "updated_at": now_iso(),
    "created_by": "user_gp08_maria",
    "actor_type": "human",
    "updated_by": "user_gp08_maria",
    "updated_actor_type": "human",
    "agent_id": None,
    "model_id": None,
    "confidence": None,
}

GP08_USER = {
    "uid": "user_gp08_maria",
    "email": "mgonzalez@lonestarinfra.com",
    "name": "Maria Gonzalez",
    "role": "owner",
    "company_id": "comp_gp08",
}

# -----------------------------------------------------------------------
# GP09 — Apartment Complex, Active Incident (UK — Scotland)
# -----------------------------------------------------------------------
GP09_COMPANY = {
    "id": "comp_gp09",
    "name": "Highland Developments Ltd",
    "address": "14 George Street, Edinburgh EH2 2PF",
    "license_number": "UK-SSIP-SC-7723",
    "trade_type": "general",
    "owner_name": "Fiona MacLeod",
    "phone": "+44-131-555-0456",
    "email": "fiona@highlanddevelopments.co.uk",
    "jurisdiction_code": "UK",
    "subscription_status": "active",
    "subscription_plan": "Professional",
    "created_at": now_iso(),
    "updated_at": now_iso(),
    "created_by": "user_gp09_fiona",
    "actor_type": "human",
    "updated_by": "user_gp09_fiona",
    "updated_actor_type": "human",
    "agent_id": None,
    "model_id": None,
    "confidence": None,
}

GP09_USER = {
    "uid": "user_gp09_fiona",
    "email": "fiona@highlanddevelopments.co.uk",
    "name": "Fiona MacLeod",
    "role": "owner",
    "company_id": "comp_gp09",
}

# -----------------------------------------------------------------------
# GP10 — Office Refurb, Closeout (AU — Victoria)
# -----------------------------------------------------------------------
GP10_COMPANY = {
    "id": "comp_gp10",
    "name": "Yarra Fitout Group Pty Ltd",
    "address": "180 Flinders Street, Melbourne, VIC 3000",
    "license_number": "AU-VIC-RBP-DB-U-44521",
    "trade_type": "general",
    "owner_name": "Ben Kowalski",
    "phone": "+61-3-9654-7788",
    "email": "ben@yarrafitout.com.au",
    "jurisdiction_code": "AU",
    "subscription_status": "active",
    "subscription_plan": "Professional",
    "created_at": now_iso(),
    "updated_at": now_iso(),
    "created_by": "user_gp10_ben",
    "actor_type": "human",
    "updated_by": "user_gp10_ben",
    "updated_actor_type": "human",
    "agent_id": None,
    "model_id": None,
    "confidence": None,
}

GP10_USER = {
    "uid": "user_gp10_ben",
    "email": "ben@yarrafitout.com.au",
    "name": "Ben Kowalski",
    "role": "owner",
    "company_id": "comp_gp10",
}

# -----------------------------------------------------------------------
# Aggregate lists for the orchestrator
# -----------------------------------------------------------------------

ALL_COMPANIES = [
    GP01_COMPANY, GP02_COMPANY, GP03_COMPANY, GP04_COMPANY, GP05_COMPANY,
    GP06_COMPANY, GP07_COMPANY, GP08_COMPANY, GP09_COMPANY, GP10_COMPANY,
]

ALL_USERS = [
    GP01_USER, GP02_USER, GP03_USER, GP04_USER, GP05_USER,
    GP06_USER, GP07_USER, GP08_USER, GP09_USER, GP10_USER,
]
