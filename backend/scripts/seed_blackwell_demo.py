"""Seed Blackwell Bathroom Remodel project lifecycle into Neo4j for Kerf demo."""

from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "fiveseasons2026")

driver = GraphDatabase.driver(URI, auth=AUTH)


def seed(tx):
    # --- Project ---
    tx.run("""
        MERGE (p:Project {id: 'proj_blackwell'})
        SET p.name = 'Blackwell Bathroom Remodel',
            p.address = '12 Birch Lane',
            p.client_name = 'Tom Blackwell',
            p.project_type = 'residential',
            p.status = 'active',
            p.description = 'Two full bathroom gut and refits - master bath and guest bath',
            p.compliance_score = 85,
            p.created_by = 'demo_user_001',
            p.deleted = false,
            p.created_at = datetime('2026-04-01T09:00:00Z'),
            p.updated_at = datetime('2026-04-14T16:00:00Z'),
            p.company_id = 'comp_gp04'
    """)
    print("[OK] Project: proj_blackwell (Blackwell Bathroom Remodel)")

    # --- Link Company -> Project ---
    result = tx.run("""
        MATCH (c {id: 'comp_gp04'})
        MATCH (p:Project {id: 'proj_blackwell'})
        MERGE (c)-[:OWNS_PROJECT]->(p)
        RETURN c.id AS company
    """)
    rec = result.single()
    if rec:
        print(f"[OK] Link: ({rec['company']})-[:OWNS_PROJECT]->(proj_blackwell)")
    else:
        print("[WARN] Company comp_gp04 not found - creating standalone link")

    # --- Worker assignments ---
    workers = [
        ("wkr_gp04_rachel_plumb", "Rachel Huang"),
        ("wkr_gp04_omar_frame", "Omar Vasquez"),
        ("wkr_gp04_luis_frame", "Luis Herrera"),
    ]
    for wid, wname in workers:
        result = tx.run("""
            MATCH (w {id: $wid})
            MATCH (p:Project {id: 'proj_blackwell'})
            MERGE (w)-[:ASSIGNED_TO_PROJECT]->(p)
            RETURN w.id AS worker
        """, wid=wid)
        rec = result.single()
        if rec:
            print(f"[OK] Worker assigned: {wname} ({wid}) -> proj_blackwell")
        else:
            print(f"[WARN] Worker {wid} ({wname}) not found in graph")

    # --- Work Items ---
    work_items = [
        {
            "id": "wi_blackwell_demo1",
            "description": "Demo and strip master bathroom",
            "hours": 12,
            "rate": 75,
            "materials_cost": 200,
            "status": "completed",
        },
        {
            "id": "wi_blackwell_plumb1",
            "description": "Rough-in plumbing - master bath",
            "hours": 16,
            "rate": 95,
            "materials_cost": 1800,
            "status": "in_progress",
        },
        {
            "id": "wi_blackwell_demo2",
            "description": "Demo and strip guest bathroom",
            "hours": 10,
            "rate": 75,
            "materials_cost": 150,
            "status": "draft",
        },
        {
            "id": "wi_blackwell_tile",
            "description": "Tile and finish - both bathrooms",
            "hours": 24,
            "rate": 85,
            "materials_cost": 3200,
            "status": "draft",
        },
    ]
    for wi in work_items:
        tx.run("""
            MATCH (p:Project {id: 'proj_blackwell'})
            CREATE (w:WorkItem {
                id: $id,
                description: $description,
                estimated_hours: $hours,
                hourly_rate: $rate,
                materials_cost: $materials_cost,
                status: $status,
                project_id: 'proj_blackwell',
                company_id: 'comp_gp04',
                created_at: datetime('2026-04-01T10:00:00Z'),
                updated_at: datetime('2026-04-14T16:00:00Z')
            })
            CREATE (p)-[:HAS_WORK_ITEM]->(w)
        """, **wi)
        total = wi["hours"] * wi["rate"] + wi["materials_cost"]
        print(f"[OK] WorkItem: {wi['id']} - {wi['description']} (${total}, {wi['status']})")

    # --- Daily Log ---
    tx.run("""
        MATCH (p:Project {id: 'proj_blackwell'})
        CREATE (dl:DailyLog {
            id: 'dl_blackwell_01',
            date: date('2026-04-14'),
            status: 'submitted',
            crew_count: 3,
            total_hours: 24,
            weather: 'clear',
            notes: 'Demo complete on master bath. Rough-in started.',
            project_id: 'proj_blackwell',
            company_id: 'comp_gp04',
            created_by: 'demo_user_001',
            created_at: datetime('2026-04-14T16:30:00Z')
        })
        CREATE (p)-[:HAS_DAILY_LOG]->(dl)
    """)
    print("[OK] DailyLog: dl_blackwell_01 (2026-04-14, 3 crew, 24h)")

    # --- Time Entries ---
    tx.run("""
        MATCH (dl:DailyLog {id: 'dl_blackwell_01'})
        CREATE (te:TimeEntry {
            id: 'te_blackwell_01',
            worker_id: 'wkr_gp04_omar_frame',
            worker_name: 'Omar Vasquez',
            start_time: '07:00',
            end_time: '15:30',
            hours: 8.5,
            work_item_id: 'wi_blackwell_demo1',
            date: date('2026-04-14'),
            project_id: 'proj_blackwell',
            company_id: 'comp_gp04'
        })
        CREATE (dl)-[:HAS_TIME_ENTRY]->(te)
    """)
    print("[OK] TimeEntry: te_blackwell_01 - Omar Vasquez 7:00-15:30 (8.5h, demo)")

    tx.run("""
        MATCH (dl:DailyLog {id: 'dl_blackwell_01'})
        CREATE (te:TimeEntry {
            id: 'te_blackwell_02',
            worker_id: 'wkr_gp04_rachel_plumb',
            worker_name: 'Rachel Huang',
            start_time: '08:00',
            end_time: '16:00',
            hours: 8.0,
            work_item_id: 'wi_blackwell_plumb1',
            date: date('2026-04-14'),
            project_id: 'proj_blackwell',
            company_id: 'comp_gp04'
        })
        CREATE (dl)-[:HAS_TIME_ENTRY]->(te)
    """)
    print("[OK] TimeEntry: te_blackwell_02 - Rachel Huang 8:00-16:00 (8h, plumbing)")

    # --- Invoice ---
    tx.run("""
        MATCH (p:Project {id: 'proj_blackwell'})
        CREATE (inv:Invoice {
            id: 'inv_blackwell_01',
            amount: 5000,
            status: 'sent',
            type: 'receivable',
            progress_pct: 30,
            project_id: 'proj_blackwell',
            company_id: 'comp_gp04',
            client_name: 'Tom Blackwell',
            created_at: datetime('2026-04-14T17:00:00Z'),
            created_by: 'demo_user_001'
        })
        CREATE (p)-[:HAS_INVOICE]->(inv)
    """)
    print("[OK] Invoice: inv_blackwell_01 ($5,000, sent, 30% progress)")

    # --- Inspection (Quality Observation) ---
    tx.run("""
        MATCH (p:Project {id: 'proj_blackwell'})
        CREATE (i:Inspection {
            id: 'insp_blackwell_01',
            type: 'quality_check',
            overall_status: 'pass',
            inspector_name: 'Rachel Huang',
            inspector_id: 'wkr_gp04_rachel_plumb',
            notes: 'Copper supply lines properly soldered, no leaks on pressure test',
            project_id: 'proj_blackwell',
            company_id: 'comp_gp04',
            created_at: datetime('2026-04-14T15:00:00Z'),
            created_by: 'wkr_gp04_rachel_plumb'
        })
        CREATE (p)-[:HAS_INSPECTION]->(i)
    """)
    print("[OK] Inspection: insp_blackwell_01 (quality_check, pass)")


def main():
    print("=" * 60)
    print("Seeding Blackwell Bathroom Remodel into Neo4j")
    print("=" * 60)

    with driver.session() as session:
        # Clean up any previous run
        session.run("""
            MATCH (p:Project {id: 'proj_blackwell'})
            OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi)
            OPTIONAL MATCH (p)-[:HAS_DAILY_LOG]->(dl)-[:HAS_TIME_ENTRY]->(te)
            OPTIONAL MATCH (p)-[:HAS_INVOICE]->(inv)
            OPTIONAL MATCH (p)-[:HAS_INSPECTION]->(insp)
            DETACH DELETE wi, te, dl, inv, insp
        """)
        print("[CLEAN] Removed previous Blackwell child nodes if any\n")

        session.execute_write(seed)

    # Verification
    print("\n" + "=" * 60)
    print("Verification")
    print("=" * 60)
    with driver.session() as session:
        counts = session.run("""
            MATCH (p:Project {id: 'proj_blackwell'})
            OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi)
            OPTIONAL MATCH (p)-[:HAS_DAILY_LOG]->(dl)
            OPTIONAL MATCH (dl)-[:HAS_TIME_ENTRY]->(te)
            OPTIONAL MATCH (p)-[:HAS_INVOICE]->(inv)
            OPTIONAL MATCH (p)-[:HAS_INSPECTION]->(insp)
            OPTIONAL MATCH (w)-[:ASSIGNED_TO_PROJECT]->(p)
            RETURN count(DISTINCT wi) AS work_items,
                   count(DISTINCT dl) AS daily_logs,
                   count(DISTINCT te) AS time_entries,
                   count(DISTINCT inv) AS invoices,
                   count(DISTINCT insp) AS inspections,
                   count(DISTINCT w) AS workers
        """).single()
        print(f"  Work Items:    {counts['work_items']}")
        print(f"  Daily Logs:    {counts['daily_logs']}")
        print(f"  Time Entries:  {counts['time_entries']}")
        print(f"  Invoices:      {counts['invoices']}")
        print(f"  Inspections:   {counts['inspections']}")
        print(f"  Workers:       {counts['workers']}")

        # Estimate total
        est = session.run("""
            MATCH (p:Project {id: 'proj_blackwell'})-[:HAS_WORK_ITEM]->(wi)
            RETURN sum(wi.estimated_hours * wi.hourly_rate + wi.materials_cost) AS estimate
        """).single()
        print(f"\n  Total Estimate: ${est['estimate']:,.0f}")

    driver.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
