"""Immutable jurisdiction context injected into services."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JurisdictionContext:
    """Immutable jurisdiction context resolved from a jurisdiction pack.

    Loaded once per request based on the company's jurisdiction_code and
    jurisdiction_region, then passed to services that need regulatory awareness.

    Args:
        code: ISO-style country code (e.g. "US", "UK", "AU", "CA").
        region: Optional sub-national region (e.g. "CA" for California, "nsw").
        manifest: Parsed manifest.yaml — country metadata, locale, metrics.
        regulations: Parsed regulations.yaml — acts, sections, penalties.
        certifications: Parsed certifications.yaml — valid cert types.
        document_types: Parsed document_types.yaml — available doc types.
        compliance_rules: Parsed compliance_rules.yaml — audit rules engine.
        region_rules: Parsed regions/{region}.yaml — sub-national additions.
        pack_dir: Filesystem path to the jurisdiction pack directory.
    """

    code: str
    region: str | None = None
    manifest: dict[str, Any] = field(default_factory=dict)
    regulations: dict[str, Any] = field(default_factory=dict)
    certifications: list[dict[str, Any]] = field(default_factory=list)
    document_types: list[dict[str, Any]] = field(default_factory=list)
    compliance_rules: dict[str, Any] = field(default_factory=dict)
    region_rules: dict[str, Any] = field(default_factory=dict)
    pack_dir: str = ""

    # -- Locale convenience accessors -------------------------------------------

    @property
    def locale(self) -> dict[str, Any]:
        """Return the locale block from the manifest."""
        return self.manifest.get("locale", {})

    @property
    def currency(self) -> str:
        """Return the currency code (e.g. 'USD', 'GBP')."""
        return self.locale.get("currency", "USD")

    @property
    def currency_symbol(self) -> str:
        """Return the currency symbol (e.g. '$', '\u00a3')."""
        return self.locale.get("currency_symbol", "$")

    @property
    def date_format(self) -> str:
        """Return the date display format (e.g. 'MM/DD/YYYY', 'DD/MM/YYYY')."""
        return self.locale.get("date_format", "MM/DD/YYYY")

    @property
    def measurement_system(self) -> str:
        """Return 'metric' or 'imperial'."""
        return self.locale.get("measurement_system", "imperial")

    @property
    def temperature_unit(self) -> str:
        """Return 'celsius' or 'fahrenheit'."""
        return self.locale.get("temperature_unit", "fahrenheit")

    @property
    def languages(self) -> list[str]:
        """Return supported language codes."""
        return self.locale.get("languages", ["en-US"])

    @property
    def phone_format(self) -> str:
        """Return the phone placeholder format."""
        return self.locale.get("phone_format", "(XXX) XXX-XXXX")

    @property
    def address_format(self) -> str:
        """Return the address format template."""
        return self.locale.get("address_format", "{line1}, {city}, {state} {zip}")

    # -- Safety metrics accessors -----------------------------------------------

    @property
    def safety_metrics(self) -> dict[str, Any]:
        """Return the safety_metrics block from the manifest."""
        return self.manifest.get("safety_metrics", {})

    @property
    def incident_rate_name(self) -> str:
        """Return the incident rate metric name (e.g. 'TRIR', 'AFR', 'LTIFR')."""
        return self.safety_metrics.get("incident_rate_name", "TRIR")

    @property
    def incident_rate_multiplier(self) -> int:
        """Return the multiplier for incident rate calculation.

        US OSHA: 200,000 (TRIR)
        UK HSE:  100,000 (AFR)
        AU:    1,000,000 (LTIFR)
        """
        return self.safety_metrics.get("incident_rate_multiplier", 200_000)

    @property
    def incident_rate_formula(self) -> str:
        """Return human-readable formula for the incident rate."""
        return self.safety_metrics.get(
            "incident_rate_formula",
            "(recordable cases * 200,000) / total hours worked",
        )

    @property
    def reporting_body(self) -> str:
        """Return the reporting body name (e.g. 'OSHA', 'HSE', 'Safe Work Australia')."""
        return self.safety_metrics.get("reporting_body", "OSHA")

    # -- Record-keeping accessors -----------------------------------------------

    @property
    def record_keeping(self) -> dict[str, Any]:
        """Return the record_keeping block from the manifest."""
        return self.manifest.get("record_keeping", {})

    @property
    def record_keeping_name(self) -> str:
        """Return the name of the incident record system.

        US: 'OSHA 300 Log'
        UK: 'RIDDOR'
        AU: 'Notifiable Incidents Register'
        """
        return self.record_keeping.get("name", "Incident Log")

    @property
    def record_keeping_feature_key(self) -> str:
        """Return the feature key for routing (e.g. 'osha_log', 'riddor')."""
        return self.record_keeping.get("feature_key", "incident_log")

    # -- Compliance audit accessors ---------------------------------------------

    @property
    def compliance_audit_name(self) -> str:
        """Return the name of the compliance audit feature.

        US: 'Mock OSHA Inspection'
        UK: 'CDM Compliance Audit'
        AU: 'WHS Compliance Audit'
        """
        return self.manifest.get("compliance_audit", {}).get(
            "name", "Compliance Audit"
        )

    @property
    def regulatory_body(self) -> str:
        """Return the regulatory body name."""
        return self.manifest.get("regulatory_body", "")

    @property
    def primary_legislation(self) -> str:
        """Return the primary legislation name."""
        return self.manifest.get("primary_legislation", "")

    @property
    def construction_legislation(self) -> str:
        """Return the construction-specific legislation name."""
        return self.manifest.get("construction_legislation", "")

    # -- Enforcement accessors --------------------------------------------------

    @property
    def enforcement(self) -> dict[str, Any]:
        """Return the enforcement block from the manifest."""
        return self.manifest.get("enforcement", {})

    # -- Data accessors ---------------------------------------------------------

    def get_certification_types(self) -> list[dict[str, Any]]:
        """Return the list of valid certification types for this jurisdiction."""
        return self.certifications

    def get_certification_by_id(self, cert_id: str) -> dict[str, Any] | None:
        """Look up a certification type by its ID."""
        for cert in self.certifications:
            if cert.get("id") == cert_id:
                return cert
        return None

    def get_document_types(self) -> list[dict[str, Any]]:
        """Return the list of available document types for this jurisdiction."""
        return self.document_types

    def get_document_type_by_id(self, doc_type_id: str) -> dict[str, Any] | None:
        """Look up a document type by its ID."""
        for dt in self.document_types:
            if dt.get("id") == doc_type_id:
                return dt
        return None

    def get_document_type_by_universal(self, universal_key: str) -> dict[str, Any] | None:
        """Look up a document type by its universal mapping key."""
        for dt in self.document_types:
            if dt.get("maps_to_universal") == universal_key:
                return dt
        return None

    def get_prompt(self, document_type_id: str) -> str:
        """Load the AI generation prompt for a document type.

        Args:
            document_type_id: The document type ID (e.g. 'sssp', 'construction_phase_plan').

        Returns:
            The system prompt text.

        Raises:
            FileNotFoundError: If the prompt file doesn't exist.
            ValueError: If the document type has no prompt_file configured.
        """
        dt = self.get_document_type_by_id(document_type_id)
        if dt is None:
            raise ValueError(
                f"Unknown document type '{document_type_id}' "
                f"for jurisdiction '{self.code}'"
            )

        prompt_file = dt.get("prompt_file")
        if not prompt_file:
            raise ValueError(
                f"Document type '{document_type_id}' has no prompt_file configured "
                f"in jurisdiction '{self.code}'"
            )

        prompt_path = Path(self.pack_dir) / prompt_file
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_path} "
                f"for document type '{document_type_id}' in jurisdiction '{self.code}'"
            )

        return prompt_path.read_text(encoding="utf-8")

    def get_trade_types(self) -> list[dict[str, str]]:
        """Return the list of trade types for this jurisdiction."""
        return self.manifest.get("trade_types", [])

    def get_prequalification_platforms(self) -> list[dict[str, str]]:
        """Return the list of prequalification platforms."""
        return self.manifest.get("prequalification_platforms", [])

    def get_compliance_required_programs(self) -> list[dict[str, Any]]:
        """Return required programs from the compliance rules."""
        return self.compliance_rules.get("required_programs", [])

    def get_compliance_required_certifications(self) -> list[dict[str, Any]]:
        """Return required certification rules from the compliance rules."""
        return self.compliance_rules.get("required_certifications", [])

    def get_compliance_inspection_requirements(self) -> list[dict[str, Any]]:
        """Return inspection requirement rules."""
        return self.compliance_rules.get("inspection_requirements", [])

    def get_compliance_training_requirements(self) -> list[dict[str, Any]]:
        """Return training requirement rules."""
        return self.compliance_rules.get("training_requirements", [])

    # -- Serialisation for API responses ----------------------------------------

    def to_api_response(self) -> dict[str, Any]:
        """Serialise jurisdiction config for the frontend API response.

        Returns a dict suitable for JSON serialisation containing all the
        information the frontend needs to adapt UI labels, formats, and options.
        """
        return {
            "code": self.code,
            "region": self.region,
            "name": self.manifest.get("name", self.code),
            "regulatory_body": self.regulatory_body,
            "primary_legislation": self.primary_legislation,
            "construction_legislation": self.construction_legislation,
            "locale": self.locale,
            "safety_metrics": self.safety_metrics,
            "record_keeping": {
                "name": self.record_keeping_name,
                "feature_key": self.record_keeping_feature_key,
                "full_name": self.record_keeping.get("full_name", ""),
            },
            "compliance_audit": {
                "name": self.compliance_audit_name,
            },
            "enforcement": self.enforcement,
            "certification_types": [
                {"id": c["id"], "name": c["name"], "expires": c.get("expires", True)}
                for c in self.certifications
            ],
            "document_types": [
                {
                    "id": dt["id"],
                    "name": dt["name"],
                    "abbreviation": dt.get("abbreviation", ""),
                    "required": dt.get("required", False),
                }
                for dt in self.document_types
            ],
            "trade_types": self.get_trade_types(),
            "prequalification_platforms": self.get_prequalification_platforms(),
        }
