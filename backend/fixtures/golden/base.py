"""Base seeder class for golden project seed scripts.

Provides common Neo4j MERGE operations for all entity types.
Subclasses override ``seed()`` to create their project-specific data.
"""

import logging
from typing import Any

from neo4j import Driver, ManagedTransaction

from backend.fixtures.golden.helpers import GOLDEN_SOURCE, now_iso

logger = logging.getLogger(__name__)


class GoldenProjectSeeder:
    """Base class for golden project seed scripts.

    Subclasses must set ``GP_SLUG``, ``COMPANY_ID``, and ``PROJECT_ID``
    and implement ``seed()``.

    Attributes:
        driver: Neo4j driver instance.
        database: Target Neo4j database name.
    """

    GP_SLUG: str = ""
    COMPANY_ID: str = ""
    PROJECT_ID: str = ""

    def __init__(self, driver: Driver, database: str = "neo4j"):
        self.driver = driver
        self.database = database

    def seed(self) -> dict[str, int]:
        """Seed all data for this golden project.

        Returns:
            Dict of entity type to count seeded.
        """
        raise NotImplementedError

    # -----------------------------------------------------------------
    # Company & Project
    # -----------------------------------------------------------------

    def seed_company(self, data: dict[str, Any]) -> None:
        """Create or merge a Company node.

        Args:
            data: Company properties including id, name, jurisdiction_code, etc.
        """
        with self.driver.session(database=self.database) as session:
            session.execute_write(self._merge_company, data)
        logger.info("[%s] Seeded company: %s", self.GP_SLUG, data["name"])

    @staticmethod
    def _merge_company(tx: ManagedTransaction, data: dict[str, Any]) -> None:
        tx.run(
            """
            MERGE (c:Company {id: $id})
            SET c += $props,
                c.source = $source
            """,
            id=data["id"],
            props=data,
            source=GOLDEN_SOURCE,
        )

    def seed_user(self, user_data: dict[str, Any]) -> None:
        """Create or merge a User node linked to the company.

        Args:
            user_data: User properties including uid, email, company_id.
        """
        with self.driver.session(database=self.database) as session:
            session.execute_write(self._merge_user, user_data)

    @staticmethod
    def _merge_user(tx: ManagedTransaction, data: dict[str, Any]) -> None:
        tx.run(
            """
            MERGE (u:User {uid: $uid})
            SET u += $props,
                u.source = $source
            MERGE (c:Company {id: $company_id})
            MERGE (u)-[:BELONGS_TO]->(c)
            """,
            uid=data["uid"],
            props=data,
            company_id=data["company_id"],
            source=GOLDEN_SOURCE,
        )

    def seed_project(self, data: dict[str, Any]) -> None:
        """Create or merge a Project node linked to a company.

        Args:
            data: Project properties including id, name, company_id.
        """
        with self.driver.session(database=self.database) as session:
            session.execute_write(self._merge_project, data)
        logger.info("[%s] Seeded project: %s", self.GP_SLUG, data["name"])

    @staticmethod
    def _merge_project(tx: ManagedTransaction, data: dict[str, Any]) -> None:
        tx.run(
            """
            MERGE (p:Project {id: $id})
            SET p += $props,
                p.source = $source
            MERGE (c:Company {id: $company_id})
            MERGE (c)-[:OWNS_PROJECT]->(p)
            """,
            id=data["id"],
            props=data,
            company_id=data["company_id"],
            source=GOLDEN_SOURCE,
        )

    # -----------------------------------------------------------------
    # Workers & Certifications
    # -----------------------------------------------------------------

    def seed_workers(self, workers: list[dict[str, Any]]) -> int:
        """Create or merge Worker nodes linked to the company.

        Args:
            workers: List of worker property dicts.

        Returns:
            Number of workers seeded.
        """
        with self.driver.session(database=self.database) as session:
            for w in workers:
                session.execute_write(self._merge_worker, w, self.COMPANY_ID)
                for cert in w.get("certifications", []):
                    session.execute_write(
                        self._merge_certification, w["id"], cert,
                    )
        logger.info("[%s] Seeded %d workers", self.GP_SLUG, len(workers))
        return len(workers)

    @staticmethod
    def _merge_worker(
        tx: ManagedTransaction, data: dict[str, Any], company_id: str,
    ) -> None:
        props = {k: v for k, v in data.items() if k != "certifications"}
        tx.run(
            """
            MERGE (w:Worker {id: $id})
            SET w += $props,
                w.company_id = $company_id,
                w.source = $source
            MERGE (c:Company {id: $company_id})
            MERGE (c)-[:EMPLOYS]->(w)
            """,
            id=data["id"],
            props=props,
            company_id=company_id,
            source=GOLDEN_SOURCE,
        )

    @staticmethod
    def _merge_certification(
        tx: ManagedTransaction, worker_id: str, cert: dict[str, Any],
    ) -> None:
        tx.run(
            """
            MERGE (cert:Certification {id: $id})
            SET cert += $props,
                cert.source = $source
            MERGE (w:Worker {id: $worker_id})
            MERGE (w)-[:HAS_CERTIFICATION]->(cert)
            """,
            id=cert["id"],
            props=cert,
            worker_id=worker_id,
            source=GOLDEN_SOURCE,
        )

    # -----------------------------------------------------------------
    # Inspections
    # -----------------------------------------------------------------

    def seed_inspections(self, inspections: list[dict[str, Any]]) -> int:
        """Create or merge Inspection nodes linked to the project.

        Args:
            inspections: List of inspection property dicts.

        Returns:
            Number of inspections seeded.
        """
        with self.driver.session(database=self.database) as session:
            for insp in inspections:
                session.execute_write(
                    self._merge_inspection, insp, self.COMPANY_ID, self.PROJECT_ID,
                )
        logger.info("[%s] Seeded %d inspections", self.GP_SLUG, len(inspections))
        return len(inspections)

    @staticmethod
    def _merge_inspection(
        tx: ManagedTransaction,
        data: dict[str, Any],
        company_id: str,
        project_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (i:Inspection {id: $id})
            SET i += $props,
                i.company_id = $company_id,
                i.project_id = $project_id,
                i.source = $source
            MERGE (p:Project {id: $project_id})
            MERGE (p)-[:HAS_INSPECTION]->(i)
            """,
            id=data["id"],
            props=data,
            company_id=company_id,
            project_id=project_id,
            source=GOLDEN_SOURCE,
        )

    # -----------------------------------------------------------------
    # Incidents
    # -----------------------------------------------------------------

    def seed_incidents(self, incidents: list[dict[str, Any]]) -> int:
        """Create or merge Incident nodes linked to the project.

        Args:
            incidents: List of incident property dicts.

        Returns:
            Number of incidents seeded.
        """
        with self.driver.session(database=self.database) as session:
            for inc in incidents:
                session.execute_write(
                    self._merge_incident, inc, self.COMPANY_ID, self.PROJECT_ID,
                )
        logger.info("[%s] Seeded %d incidents", self.GP_SLUG, len(incidents))
        return len(incidents)

    @staticmethod
    def _merge_incident(
        tx: ManagedTransaction,
        data: dict[str, Any],
        company_id: str,
        project_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (i:Incident {id: $id})
            SET i += $props,
                i.company_id = $company_id,
                i.project_id = $project_id,
                i.source = $source
            MERGE (p:Project {id: $project_id})
            MERGE (p)-[:HAS_INCIDENT]->(i)
            """,
            id=data["id"],
            props=data,
            company_id=company_id,
            project_id=project_id,
            source=GOLDEN_SOURCE,
        )

    # -----------------------------------------------------------------
    # Equipment
    # -----------------------------------------------------------------

    def seed_equipment(self, equipment: list[dict[str, Any]]) -> int:
        """Create or merge Equipment nodes linked to the company.

        Args:
            equipment: List of equipment property dicts.

        Returns:
            Number of equipment items seeded.
        """
        with self.driver.session(database=self.database) as session:
            for eq in equipment:
                session.execute_write(
                    self._merge_equipment, eq, self.COMPANY_ID,
                )
        logger.info("[%s] Seeded %d equipment", self.GP_SLUG, len(equipment))
        return len(equipment)

    @staticmethod
    def _merge_equipment(
        tx: ManagedTransaction, data: dict[str, Any], company_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (e:Equipment {id: $id})
            SET e += $props,
                e.company_id = $company_id,
                e.source = $source
            MERGE (c:Company {id: $company_id})
            MERGE (c)-[:HAS_EQUIPMENT]->(e)
            """,
            id=data["id"],
            props=data,
            company_id=company_id,
            source=GOLDEN_SOURCE,
        )

    # -----------------------------------------------------------------
    # Toolbox Talks
    # -----------------------------------------------------------------

    def seed_toolbox_talks(self, talks: list[dict[str, Any]]) -> int:
        """Create or merge ToolboxTalk nodes linked to the project.

        Args:
            talks: List of toolbox talk property dicts.

        Returns:
            Number of talks seeded.
        """
        with self.driver.session(database=self.database) as session:
            for talk in talks:
                session.execute_write(
                    self._merge_toolbox_talk, talk, self.COMPANY_ID, self.PROJECT_ID,
                )
        logger.info("[%s] Seeded %d toolbox talks", self.GP_SLUG, len(talks))
        return len(talks)

    @staticmethod
    def _merge_toolbox_talk(
        tx: ManagedTransaction,
        data: dict[str, Any],
        company_id: str,
        project_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (t:ToolboxTalk {id: $id})
            SET t += $props,
                t.company_id = $company_id,
                t.project_id = $project_id,
                t.source = $source
            MERGE (p:Project {id: $project_id})
            MERGE (p)-[:HAS_TOOLBOX_TALK]->(t)
            """,
            id=data["id"],
            props=data,
            company_id=company_id,
            project_id=project_id,
            source=GOLDEN_SOURCE,
        )

    # -----------------------------------------------------------------
    # Hazard Reports
    # -----------------------------------------------------------------

    def seed_hazard_reports(self, reports: list[dict[str, Any]]) -> int:
        """Create or merge HazardReport nodes linked to the project.

        Args:
            reports: List of hazard report property dicts.

        Returns:
            Number of reports seeded.
        """
        with self.driver.session(database=self.database) as session:
            for rpt in reports:
                session.execute_write(
                    self._merge_hazard_report, rpt, self.COMPANY_ID, self.PROJECT_ID,
                )
        logger.info("[%s] Seeded %d hazard reports", self.GP_SLUG, len(reports))
        return len(reports)

    @staticmethod
    def _merge_hazard_report(
        tx: ManagedTransaction,
        data: dict[str, Any],
        company_id: str,
        project_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (h:HazardReport {id: $id})
            SET h += $props,
                h.company_id = $company_id,
                h.project_id = $project_id,
                h.source = $source
            MERGE (p:Project {id: $project_id})
            MERGE (p)-[:HAS_HAZARD_REPORT]->(h)
            """,
            id=data["id"],
            props=data,
            company_id=company_id,
            project_id=project_id,
            source=GOLDEN_SOURCE,
        )

    # -----------------------------------------------------------------
    # Daily Logs
    # -----------------------------------------------------------------

    def seed_daily_logs(self, logs: list[dict[str, Any]]) -> int:
        """Create or merge DailyLog nodes linked to the project.

        Args:
            logs: List of daily log property dicts.

        Returns:
            Number of logs seeded.
        """
        with self.driver.session(database=self.database) as session:
            for log in logs:
                session.execute_write(
                    self._merge_daily_log, log, self.COMPANY_ID, self.PROJECT_ID,
                )
        logger.info("[%s] Seeded %d daily logs", self.GP_SLUG, len(logs))
        return len(logs)

    @staticmethod
    def _merge_daily_log(
        tx: ManagedTransaction,
        data: dict[str, Any],
        company_id: str,
        project_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (d:DailyLog {id: $id})
            SET d += $props,
                d.company_id = $company_id,
                d.project_id = $project_id,
                d.source = $source
            MERGE (p:Project {id: $project_id})
            MERGE (p)-[:HAS_DAILY_LOG]->(d)
            """,
            id=data["id"],
            props=data,
            company_id=company_id,
            project_id=project_id,
            source=GOLDEN_SOURCE,
        )

    # -----------------------------------------------------------------
    # Deficiency Lists (punch lists)
    # -----------------------------------------------------------------

    def seed_deficiency_lists(self, lists: list[dict[str, Any]]) -> int:
        """Create or merge DeficiencyList nodes linked to the project.

        Args:
            lists: List of deficiency list property dicts.

        Returns:
            Number of deficiency lists seeded.
        """
        with self.driver.session(database=self.database) as session:
            for dl in lists:
                session.execute_write(
                    self._merge_deficiency_list, dl, self.COMPANY_ID, self.PROJECT_ID,
                )
        logger.info("[%s] Seeded %d deficiency lists", self.GP_SLUG, len(lists))
        return len(lists)

    @staticmethod
    def _merge_deficiency_list(
        tx: ManagedTransaction,
        data: dict[str, Any],
        company_id: str,
        project_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (d:DeficiencyList {id: $id})
            SET d += $props,
                d.company_id = $company_id,
                d.project_id = $project_id,
                d.source = $source
            MERGE (p:Project {id: $project_id})
            MERGE (p)-[:HAS_DEFICIENCY_LIST]->(d)
            """,
            id=data["id"],
            props=data,
            company_id=company_id,
            project_id=project_id,
            source=GOLDEN_SOURCE,
        )

    def seed_deficiency_items(
        self, items: list[dict[str, Any]], list_id: str,
    ) -> int:
        """Create or merge DeficiencyItem nodes linked to a DeficiencyList.

        Args:
            items: List of deficiency item property dicts.
            list_id: Parent DeficiencyList ID.

        Returns:
            Number of deficiency items seeded.
        """
        with self.driver.session(database=self.database) as session:
            for item in items:
                session.execute_write(
                    self._merge_deficiency_item, item, list_id,
                )
        logger.info("[%s] Seeded %d deficiency items", self.GP_SLUG, len(items))
        return len(items)

    @staticmethod
    def _merge_deficiency_item(
        tx: ManagedTransaction, data: dict[str, Any], list_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (di:DeficiencyItem {id: $id})
            SET di += $props,
                di.source = $source
            MERGE (dl:DeficiencyList {id: $list_id})
            MERGE (dl)-[:HAS_ITEM]->(di)
            """,
            id=data["id"],
            props=data,
            list_id=list_id,
            source=GOLDEN_SOURCE,
        )

    # -----------------------------------------------------------------
    # RFIs (Requests for Information)
    # -----------------------------------------------------------------

    def seed_rfis(self, rfis: list[dict[str, Any]]) -> int:
        """Create or merge RFI nodes linked to the project.

        Args:
            rfis: List of RFI property dicts.

        Returns:
            Number of RFIs seeded.
        """
        with self.driver.session(database=self.database) as session:
            for rfi in rfis:
                session.execute_write(
                    self._merge_rfi, rfi, self.COMPANY_ID, self.PROJECT_ID,
                )
        logger.info("[%s] Seeded %d RFIs", self.GP_SLUG, len(rfis))
        return len(rfis)

    @staticmethod
    def _merge_rfi(
        tx: ManagedTransaction,
        data: dict[str, Any],
        company_id: str,
        project_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (r:RFI {id: $id})
            SET r += $props,
                r.company_id = $company_id,
                r.project_id = $project_id,
                r.source = $source
            MERGE (p:Project {id: $project_id})
            MERGE (p)-[:HAS_RFI]->(r)
            """,
            id=data["id"],
            props=data,
            company_id=company_id,
            project_id=project_id,
            source=GOLDEN_SOURCE,
        )

    # -----------------------------------------------------------------
    # Work Items with Labour & Item children
    # -----------------------------------------------------------------

    def seed_work_items(self, work_items: list[dict[str, Any]]) -> int:
        """Create or merge WorkItem nodes with Labour and Item children.

        Each work_item dict may contain 'labour' and 'items' lists for children.

        Args:
            work_items: List of work item dicts with optional children.

        Returns:
            Number of work items seeded.
        """
        with self.driver.session(database=self.database) as session:
            for wi in work_items:
                session.execute_write(
                    self._merge_work_item, wi, self.COMPANY_ID, self.PROJECT_ID,
                )
                for lab in wi.get("labour", []):
                    session.execute_write(self._merge_labour, lab, wi["id"])
                for item in wi.get("items", []):
                    session.execute_write(self._merge_item, item, wi["id"])
        logger.info("[%s] Seeded %d work items", self.GP_SLUG, len(work_items))
        return len(work_items)

    @staticmethod
    def _merge_work_item(
        tx: ManagedTransaction, data: dict[str, Any],
        company_id: str, project_id: str,
    ) -> None:
        props = {k: v for k, v in data.items() if k not in ("labour", "items")}
        tx.run(
            """
            MERGE (wi:WorkItem {id: $id})
            SET wi += $props,
                wi.source = $source
            MERGE (p:Project {id: $project_id})
            MERGE (p)-[:HAS_WORK_ITEM]->(wi)
            """,
            id=data["id"], props=props, project_id=project_id,
            source=GOLDEN_SOURCE,
        )

    @staticmethod
    def _merge_labour(
        tx: ManagedTransaction, data: dict[str, Any], work_item_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (lab:Labour {id: $id})
            SET lab += $props,
                lab.source = $source
            MERGE (wi:WorkItem {id: $work_item_id})
            MERGE (wi)-[:HAS_LABOUR]->(lab)
            """,
            id=data["id"], props=data, work_item_id=work_item_id,
            source=GOLDEN_SOURCE,
        )

    @staticmethod
    def _merge_item(
        tx: ManagedTransaction, data: dict[str, Any], work_item_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (item:Item {id: $id})
            SET item += $props,
                item.source = $source
            MERGE (wi:WorkItem {id: $work_item_id})
            MERGE (wi)-[:HAS_ITEM]->(item)
            """,
            id=data["id"], props=data, work_item_id=work_item_id,
            source=GOLDEN_SOURCE,
        )

    # -----------------------------------------------------------------
    # Assumptions & Exclusions
    # -----------------------------------------------------------------

    def seed_assumptions(self, assumptions: list[dict[str, Any]]) -> int:
        """Create or merge Assumption nodes on the project.

        Args:
            assumptions: List of assumption dicts.

        Returns:
            Number of assumptions seeded.
        """
        with self.driver.session(database=self.database) as session:
            for a in assumptions:
                session.execute_write(
                    self._merge_assumption, a, self.COMPANY_ID, self.PROJECT_ID,
                )
        logger.info("[%s] Seeded %d assumptions", self.GP_SLUG, len(assumptions))
        return len(assumptions)

    @staticmethod
    def _merge_assumption(
        tx: ManagedTransaction, data: dict[str, Any],
        company_id: str, project_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (a:Assumption {id: $id})
            SET a += $props,
                a.source = $source
            MERGE (p:Project {id: $project_id})
            MERGE (p)-[:HAS_ASSUMPTION]->(a)
            """,
            id=data["id"], props=data, project_id=project_id,
            source=GOLDEN_SOURCE,
        )

    def seed_exclusions(self, exclusions: list[dict[str, Any]]) -> int:
        """Create or merge Exclusion nodes on the project.

        Args:
            exclusions: List of exclusion dicts.

        Returns:
            Number of exclusions seeded.
        """
        with self.driver.session(database=self.database) as session:
            for e in exclusions:
                session.execute_write(
                    self._merge_exclusion, e, self.COMPANY_ID, self.PROJECT_ID,
                )
        logger.info("[%s] Seeded %d exclusions", self.GP_SLUG, len(exclusions))
        return len(exclusions)

    @staticmethod
    def _merge_exclusion(
        tx: ManagedTransaction, data: dict[str, Any],
        company_id: str, project_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (e:Exclusion {id: $id})
            SET e += $props,
                e.source = $source
            MERGE (p:Project {id: $project_id})
            MERGE (p)-[:HAS_EXCLUSION]->(e)
            """,
            id=data["id"], props=data, project_id=project_id,
            source=GOLDEN_SOURCE,
        )

    # -----------------------------------------------------------------
    # Assumption & Exclusion Templates (company-level)
    # -----------------------------------------------------------------

    def seed_assumption_templates(self, templates: list[dict[str, Any]]) -> int:
        """Create or merge company-level Assumption templates.

        Args:
            templates: List of template dicts.

        Returns:
            Number of templates seeded.
        """
        with self.driver.session(database=self.database) as session:
            for t in templates:
                session.execute_write(
                    self._merge_assumption_template, t, self.COMPANY_ID,
                )
        logger.info("[%s] Seeded %d assumption templates", self.GP_SLUG, len(templates))
        return len(templates)

    @staticmethod
    def _merge_assumption_template(
        tx: ManagedTransaction, data: dict[str, Any], company_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (a:Assumption {id: $id})
            SET a += $props,
                a.is_template = true,
                a.source = $source
            MERGE (c:Company {id: $company_id})
            MERGE (c)-[:ASSUMPTION_TEMPLATE_OF]->(a)
            """,
            id=data["id"], props=data, company_id=company_id,
            source=GOLDEN_SOURCE,
        )

    def seed_exclusion_templates(self, templates: list[dict[str, Any]]) -> int:
        """Create or merge company-level Exclusion templates.

        Args:
            templates: List of template dicts.

        Returns:
            Number of templates seeded.
        """
        with self.driver.session(database=self.database) as session:
            for t in templates:
                session.execute_write(
                    self._merge_exclusion_template, t, self.COMPANY_ID,
                )
        logger.info("[%s] Seeded %d exclusion templates", self.GP_SLUG, len(templates))
        return len(templates)

    @staticmethod
    def _merge_exclusion_template(
        tx: ManagedTransaction, data: dict[str, Any], company_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (e:Exclusion {id: $id})
            SET e += $props,
                e.is_template = true,
                e.source = $source
            MERGE (c:Company {id: $company_id})
            MERGE (c)-[:EXCLUSION_TEMPLATE_OF]->(e)
            """,
            id=data["id"], props=data, company_id=company_id,
            source=GOLDEN_SOURCE,
        )

    # -----------------------------------------------------------------
    # Contract, Payment Milestones, Conditions, Warranty
    # -----------------------------------------------------------------

    def seed_contract(self, data: dict[str, Any], project_id: str | None = None) -> None:
        """Create or merge a Contract node linked to a project.

        Args:
            data: Contract properties including id, retention_pct, payment_terms_days.
            project_id: Project ID (defaults to self.PROJECT_ID).
        """
        pid = project_id or self.PROJECT_ID
        with self.driver.session(database=self.database) as session:
            session.execute_write(self._merge_contract, data, pid)
        logger.info("[%s] Seeded contract: %s", self.GP_SLUG, data["id"])

    @staticmethod
    def _merge_contract(
        tx: ManagedTransaction, data: dict[str, Any], project_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (ct:Contract {id: $id})
            SET ct += $props,
                ct.source = $source
            MERGE (p:Project {id: $project_id})
            MERGE (p)-[:HAS_CONTRACT]->(ct)
            """,
            id=data["id"], props=data, project_id=project_id,
            source=GOLDEN_SOURCE,
        )

    def seed_payment_milestones(
        self, milestones: list[dict[str, Any]], contract_id: str,
    ) -> int:
        """Create or merge PaymentMilestone nodes linked to a Contract.

        Args:
            milestones: List of milestone property dicts.
            contract_id: Parent Contract ID.

        Returns:
            Number of milestones seeded.
        """
        with self.driver.session(database=self.database) as session:
            for m in milestones:
                session.execute_write(
                    self._merge_payment_milestone, m, contract_id,
                )
        logger.info(
            "[%s] Seeded %d payment milestones", self.GP_SLUG, len(milestones),
        )
        return len(milestones)

    @staticmethod
    def _merge_payment_milestone(
        tx: ManagedTransaction, data: dict[str, Any], contract_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (pm:PaymentMilestone {id: $id})
            SET pm += $props,
                pm.source = $source
            MERGE (ct:Contract {id: $contract_id})
            MERGE (ct)-[:HAS_MILESTONE]->(pm)
            """,
            id=data["id"], props=data, contract_id=contract_id,
            source=GOLDEN_SOURCE,
        )

    def seed_conditions(
        self, conditions: list[dict[str, Any]], contract_id: str,
    ) -> int:
        """Create or merge Condition nodes linked to a Contract.

        Args:
            conditions: List of condition property dicts.
            contract_id: Parent Contract ID.

        Returns:
            Number of conditions seeded.
        """
        with self.driver.session(database=self.database) as session:
            for c in conditions:
                session.execute_write(
                    self._merge_condition, c, contract_id,
                )
        logger.info(
            "[%s] Seeded %d conditions", self.GP_SLUG, len(conditions),
        )
        return len(conditions)

    @staticmethod
    def _merge_condition(
        tx: ManagedTransaction, data: dict[str, Any], contract_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (cond:Condition {id: $id})
            SET cond += $props,
                cond.source = $source
            MERGE (ct:Contract {id: $contract_id})
            MERGE (ct)-[:HAS_CONDITION]->(cond)
            """,
            id=data["id"], props=data, contract_id=contract_id,
            source=GOLDEN_SOURCE,
        )

    def seed_warranty(
        self, data: dict[str, Any], contract_id: str,
    ) -> None:
        """Create or merge a Warranty node linked to a Contract.

        Args:
            data: Warranty properties including id, period_months, scope, etc.
            contract_id: Parent Contract ID.
        """
        with self.driver.session(database=self.database) as session:
            session.execute_write(self._merge_warranty, data, contract_id)
        logger.info("[%s] Seeded warranty: %s", self.GP_SLUG, data["id"])

    @staticmethod
    def _merge_warranty(
        tx: ManagedTransaction, data: dict[str, Any], contract_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (w:Warranty {id: $id})
            SET w += $props,
                w.source = $source
            MERGE (ct:Contract {id: $contract_id})
            MERGE (ct)-[:HAS_WARRANTY]->(w)
            """,
            id=data["id"], props=data, contract_id=contract_id,
            source=GOLDEN_SOURCE,
        )

    # -----------------------------------------------------------------
    # Resource Rates & Productivity Rates (company-level)
    # -----------------------------------------------------------------

    def seed_resource_rates(self, rates: list[dict[str, Any]]) -> int:
        """Create or merge ResourceRate nodes at the company level.

        Args:
            rates: List of rate dicts.

        Returns:
            Number of rates seeded.
        """
        with self.driver.session(database=self.database) as session:
            for r in rates:
                session.execute_write(
                    self._merge_resource_rate, r, self.COMPANY_ID,
                )
        logger.info("[%s] Seeded %d resource rates", self.GP_SLUG, len(rates))
        return len(rates)

    @staticmethod
    def _merge_resource_rate(
        tx: ManagedTransaction, data: dict[str, Any], company_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (rr:ResourceRate {id: $id})
            SET rr += $props,
                rr.source_tag = $source
            MERGE (c:Company {id: $company_id})
            MERGE (c)-[:HAS_RATE]->(rr)
            """,
            id=data["id"], props=data, company_id=company_id,
            source=GOLDEN_SOURCE,
        )

    def seed_productivity_rates(self, rates: list[dict[str, Any]]) -> int:
        """Create or merge ProductivityRate nodes at the company level.

        Args:
            rates: List of rate dicts.

        Returns:
            Number of rates seeded.
        """
        with self.driver.session(database=self.database) as session:
            for r in rates:
                session.execute_write(
                    self._merge_productivity_rate, r, self.COMPANY_ID,
                )
        logger.info("[%s] Seeded %d productivity rates", self.GP_SLUG, len(rates))
        return len(rates)

    @staticmethod
    def _merge_productivity_rate(
        tx: ManagedTransaction, data: dict[str, Any], company_id: str,
    ) -> None:
        tx.run(
            """
            MERGE (pr:ProductivityRate {id: $id})
            SET pr += $props,
                pr.source_tag = $source
            MERGE (c:Company {id: $company_id})
            MERGE (c)-[:HAS_PRODUCTIVITY]->(pr)
            """,
            id=data["id"], props=data, company_id=company_id,
            source=GOLDEN_SOURCE,
        )

    # -----------------------------------------------------------------
    # Worker ↔ Project assignment
    # -----------------------------------------------------------------

    def assign_workers_to_project(
        self, worker_ids: list[str], project_id: str | None = None,
    ) -> None:
        """Create ASSIGNED_TO_PROJECT relationships between workers and a project.

        Args:
            worker_ids: List of worker IDs to assign.
            project_id: Project ID (defaults to self.PROJECT_ID).
        """
        pid = project_id or self.PROJECT_ID
        with self.driver.session(database=self.database) as session:
            for wid in worker_ids:
                session.execute_write(self._assign_worker, wid, pid)

    @staticmethod
    def _assign_worker(
        tx: ManagedTransaction, worker_id: str, project_id: str,
    ) -> None:
        tx.run(
            """
            MATCH (w:Worker {id: $worker_id})
            MATCH (p:Project {id: $project_id})
            MERGE (w)-[:ASSIGNED_TO_PROJECT]->(p)
            """,
            worker_id=worker_id,
            project_id=project_id,
        )
