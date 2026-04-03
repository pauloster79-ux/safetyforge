"""Loads jurisdiction packs from YAML files with LRU caching."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.jurisdiction.context import JurisdictionContext

logger = logging.getLogger(__name__)

# Resolve the jurisdictions directory relative to this file.
# Structure: backend/app/jurisdiction/loader.py -> backend/jurisdictions/
_JURISDICTIONS_DIR = Path(__file__).resolve().parent.parent.parent / "jurisdictions"


def _load_yaml(path: Path) -> dict[str, Any] | list[dict[str, Any]]:
    """Load and parse a YAML file.

    Args:
        path: Absolute path to the YAML file.

    Returns:
        Parsed YAML content.

    Raises:
        FileNotFoundError: If the file doesn't exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Jurisdiction file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class JurisdictionLoader:
    """Loads and caches jurisdiction packs from the filesystem.

    Jurisdiction packs live under backend/jurisdictions/{code}/ and contain
    YAML files defining the regulatory framework, certifications, document
    types, compliance rules, and AI generation prompts for a country.
    """

    _cache: dict[str, JurisdictionContext] = {}

    @classmethod
    def load(cls, code: str, region: str | None = None) -> JurisdictionContext:
        """Load a jurisdiction context by country code and optional region.

        Results are cached by (code, region) tuple. Subsequent calls with
        the same arguments return the cached instance.

        Args:
            code: Country code (e.g. "US", "UK", "AU", "CA").
            region: Optional sub-national region code (e.g. "CA", "nsw").

        Returns:
            An immutable JurisdictionContext instance.

        Raises:
            FileNotFoundError: If the jurisdiction pack doesn't exist.
            ValueError: If required files are missing from the pack.
        """
        cache_key = f"{code}:{region or ''}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        code_lower = code.lower()
        pack_dir = _JURISDICTIONS_DIR / code_lower

        if not pack_dir.is_dir():
            raise FileNotFoundError(
                f"Jurisdiction pack not found for code '{code}'. "
                f"Expected directory: {pack_dir}"
            )

        # Load required manifest
        manifest_path = pack_dir / "manifest.yaml"
        manifest = _load_yaml(manifest_path)
        if not isinstance(manifest, dict):
            raise ValueError(f"manifest.yaml must be a dict, got {type(manifest)}")

        # Load optional files (empty defaults if missing)
        certifications_raw = cls._load_optional(pack_dir / "certifications.yaml", {})
        certifications = certifications_raw.get("certifications", []) if isinstance(certifications_raw, dict) else []

        doc_types_raw = cls._load_optional(pack_dir / "document_types.yaml", {})
        document_types = doc_types_raw.get("document_types", []) if isinstance(doc_types_raw, dict) else []

        compliance_rules = cls._load_optional(pack_dir / "compliance_rules.yaml", {})
        if not isinstance(compliance_rules, dict):
            compliance_rules = {}

        regulations = cls._load_optional(pack_dir / "regulations.yaml", {})
        if not isinstance(regulations, dict):
            regulations = {}

        # Load optional region-specific rules
        region_rules: dict[str, Any] = {}
        if region:
            region_path = pack_dir / "regions" / f"{region.lower()}.yaml"
            if region_path.exists():
                region_data = _load_yaml(region_path)
                region_rules = region_data if isinstance(region_data, dict) else {}
            else:
                logger.info(
                    "No region file for %s/%s — using country-level rules only",
                    code,
                    region,
                )

        ctx = JurisdictionContext(
            code=code.upper(),
            region=region,
            manifest=manifest,
            regulations=regulations,
            certifications=certifications,
            document_types=document_types,
            compliance_rules=compliance_rules,
            region_rules=region_rules,
            pack_dir=str(pack_dir),
        )

        cls._cache[cache_key] = ctx
        logger.info("Loaded jurisdiction pack: %s (region=%s)", code, region)
        return ctx

    @classmethod
    def available_jurisdictions(cls) -> list[dict[str, Any]]:
        """Return a list of available jurisdiction codes and names.

        Scans the jurisdictions directory for valid packs (directories
        containing a manifest.yaml).

        Returns:
            A list of dicts with 'code', 'name', and 'regulatory_body' keys.
        """
        results = []
        if not _JURISDICTIONS_DIR.is_dir():
            return results

        for child in sorted(_JURISDICTIONS_DIR.iterdir()):
            if not child.is_dir():
                continue
            manifest_path = child / "manifest.yaml"
            if not manifest_path.exists():
                continue
            try:
                manifest = _load_yaml(manifest_path)
                if isinstance(manifest, dict):
                    results.append(
                        {
                            "code": manifest.get("code", child.name.upper()),
                            "name": manifest.get("name", child.name),
                            "regulatory_body": manifest.get("regulatory_body", ""),
                        }
                    )
            except Exception:
                logger.warning("Failed to load manifest for %s", child.name, exc_info=True)

        return results

    @classmethod
    def available_regions(cls, code: str) -> list[dict[str, str]]:
        """Return available sub-national regions for a jurisdiction.

        Args:
            code: Country code.

        Returns:
            A list of dicts with 'code' and 'name' keys.
        """
        pack_dir = _JURISDICTIONS_DIR / code.lower()
        regions_dir = pack_dir / "regions"
        if not regions_dir.is_dir():
            return []

        results = []
        for yaml_file in sorted(regions_dir.glob("*.yaml")):
            try:
                data = _load_yaml(yaml_file)
                if isinstance(data, dict):
                    results.append(
                        {
                            "code": data.get("code", yaml_file.stem),
                            "name": data.get("name", yaml_file.stem),
                        }
                    )
            except Exception:
                logger.warning("Failed to load region %s", yaml_file, exc_info=True)

        return results

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the jurisdiction cache.

        Useful for testing or after hot-reloading jurisdiction pack files.
        """
        cls._cache.clear()

    @classmethod
    def _load_optional(cls, path: Path, default: Any) -> Any:
        """Load a YAML file, returning a default if it doesn't exist.

        Args:
            path: Path to the YAML file.
            default: Value to return if the file is missing.

        Returns:
            Parsed YAML content or the default value.
        """
        if not path.exists():
            return default
        try:
            return _load_yaml(path)
        except Exception:
            logger.warning("Failed to load %s, using default", path, exc_info=True)
            return default
