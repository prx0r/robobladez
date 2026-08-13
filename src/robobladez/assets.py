"""Canonical visual asset system (rmart / RoboBladez visual stack).

The goal is NOT `prompt -> image -> use once`. It is:

    GAME STATE / CANON -> VISUAL SPEC -> ASSET GENERATOR -> CANDIDATES
      -> VALIDATION -> CANONICAL ASSET VERSION -> ASSET GRAPH
      -> SHOT COMPILER -> IMAGE/VIDEO/UI/POSTER/THUMBNAIL -> REUSE

Constitution rule (rmart §central rule):
    "Generative models may propose visual reality. Only the canon system may
     establish it. Once visual reality is established, downstream generators
     reference it rather than reinventing it."

Every persistent thing has two representations:
    STRUCTURAL STATE (what it is)  -> mechanical/gameplay truth
    VISUAL STATE (how it appears)  -> canonical presentation truth

This module implements the MVP ontology (rmart §37): VisualSpec,
CanonicalVisualAsset, StyleProfile, AssetResolver, VisualForge, ShotAssetBundle.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
import hashlib, json

ASSET_TYPES = (
    "AGENT_PORTRAIT", "TALISMAN", "DAIMON", "ARENA", "EFFECT",
    "WORLD", "POSTER", "THUMBNAIL", "EDITORIAL", "SIGIL", "ICON",
)
CANONICALITY = ("CANONICAL", "PROJECTION", "EDITORIAL")
VIEWS = ("HERO", "FRONT", "SIDE", "TOP", "THREE_QUARTER", "REAR", "DETAIL", "ISOLATED")
ASSET_STATUS = ("DRAFT", "CANDIDATE", "APPROVED", "SUPERSEDED", "RETIRED")


@dataclass(frozen=True)
class VisualAsset:
    """A versioned, hash-addressed canonical visual asset.

    `mechanical_version` ties this image to the exact gameplay body/Daimon it
    represents, so we can say "this image shows BORIS_TALISMAN mechanical R17,
    visual R4" (rmart §8).
    """
    id: str
    asset_type: str                       # one of ASSET_TYPES
    entity_id: str = ""                   # "boris", "penelope", "arena-s1"
    version: int = 1
    status: str = "DRAFT"                 # ASSET_STATUS
    canonicality: str = "EDITORIAL"       # CANONICALITY
    identity_version: str = "R0"          # visual identity lineage
    mechanical_version: str = ""          # gameplay body/Daimon version
    prompt_spec_id: str = ""
    reference_asset_ids: list[str] = field(default_factory=list)
    generator_family: str = ""
    generator_version: str = ""
    seed: int = 0
    file_uri: str = ""
    thumbnail_uri: str = ""
    alpha_uri: str = ""
    depth_uri: str = ""
    mask_uri: str = ""
    view: str = "HERO"                    # one of VIEWS
    created_at: str = ""
    supersedes: str = ""
    qa_score: float = 0.0
    review_status: str = ""
    tags: list[str] = field(default_factory=list)

    def asset_key(self) -> str:
        """Stable identity: type + entity + view + version."""
        return f"{self.asset_type}:{self.entity_id}:{self.view}:R{self.version}"

    def digest(self) -> str:
        """Hash over canonical (non-narrative) fields; used to pin assets in shots."""
        body = {
            "asset_type": self.asset_type, "entity_id": self.entity_id,
            "version": self.version, "view": self.view,
            "canonicality": self.canonicality, "mechanical_version": self.mechanical_version,
            "identity_version": self.identity_version, "file_uri": self.file_uri,
        }
        return hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:20]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["asset_key"] = self.asset_key()
        d["digest"] = self.digest()
        return d


@dataclass
class VisualSpec:
    """Machine-readable spec that drives generation (rmart §9).

    The prompt is compiled FROM the spec; the spec is the source of truth, never
    the prompt. Kept provider-agnostic so generators are replaceable.
    """
    spec_id: str
    entity_id: str
    asset_type: str = "TALISMAN"
    mechanical_version: str = ""
    view: str = "HERO"
    silhouette: str = ""
    visual_weight: str = ""
    symmetry: str = ""
    personality: str = ""
    materials: list[str] = field(default_factory=list)
    palette: list[str] = field(default_factory=list)
    motifs: list[str] = field(default_factory=list)
    forbidden: list[str] = field(default_factory=list)
    required_views: list[str] = field(default_factory=lambda: ["HERO", "SIDE", "TOP", "THREE_QUARTER"])
    style_profile: str = "RBZ_CINEMATIC_S01"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StyleProfile:
    """Reusable rendering medium / style (rmart §22)."""
    id: str
    rendering_medium: str = "cinematic"
    contrast: str = "medium"
    lighting: str = "cool-white"
    palette_transforms: list[str] = field(default_factory=list)
    texture: str = "clean"
    background_behavior: str = "isolated"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AssetLibrary:
    """Versioned, append-only canonical + editorial asset store."""

    def __init__(self):
        self._assets: dict[str, VisualAsset] = {}

    def add(self, asset: VisualAsset) -> VisualAsset:
        key = asset.asset_key()
        if key in self._assets:
            return self._assets[key]
        self._assets[key] = asset
        return asset

    def approve(self, key: str) -> VisualAsset:
        a = self._assets[key]
        approved = VisualAsset(
            id=a.id, asset_type=a.asset_type, entity_id=a.entity_id,
            version=a.version, status="APPROVED", canonicality="CANONICAL",
            identity_version=a.identity_version, mechanical_version=a.mechanical_version,
            prompt_spec_id=a.prompt_spec_id, reference_asset_ids=a.reference_asset_ids,
            generator_family=a.generator_family, generator_version=a.generator_version,
            seed=a.seed, file_uri=a.file_uri, thumbnail_uri=a.thumbnail_uri,
            alpha_uri=a.alpha_uri, depth_uri=a.depth_uri, mask_uri=a.mask_uri,
            view=a.view, created_at=a.created_at, supersedes=a.supersedes,
            qa_score=a.qa_score, review_status=a.review_status, tags=a.tags,
        )
        self._assets[key] = approved
        return approved

    def get(self, key: str) -> VisualAsset | None:
        return self._assets.get(key)

    def latest_canonical(self, entity_id: str, asset_type: str,
                         view: str = "HERO") -> VisualAsset | None:
        best = None
        for a in self._assets.values():
            if (a.entity_id == entity_id and a.asset_type == asset_type
                    and a.view == view and a.canonicality == "CANONICAL"
                    and a.status == "APPROVED"):
                if best is None or a.version > best.version:
                    best = a
        return best

    def references_for(self, entity_id: str, view: str | None = None) -> list[VisualAsset]:
        return [a for a in self._assets.values()
                if a.entity_id == entity_id and a.canonicality == "CANONICAL"
                and (view is None or a.view == view)]

    def all(self) -> list[VisualAsset]:
        return list(self._assets.values())


class AssetResolver:
    """Given a query, return the canonical reference bundle (rmart §15)."""

    def __init__(self, library: AssetLibrary):
        self.library = library

    def resolve(self, *, entity: str, asset_type: str = "TALISMAN",
                body_version: str = "", daimon_stage: str = "",
                ability: str = "", arena: str = "") -> list[dict]:
        refs = []
        for asset in self.library.references_for(entity):
            refs.append({"type": asset.asset_type, "view": asset.view,
                         "asset_key": asset.asset_key(), "uri": asset.file_uri,
                         "digest": asset.digest()})
        if arena:
            for asset in self.library.references_for(arena):
                refs.append({"type": asset.asset_type, "view": asset.view,
                             "asset_key": asset.asset_key(), "uri": asset.file_uri,
                             "digest": asset.digest()})
        if ability:
            for asset in self.library.references_for(ability):
                refs.append({"type": asset.asset_type, "view": asset.view,
                             "asset_key": asset.asset_key(), "uri": asset.file_uri,
                             "digest": asset.digest()})
        return refs


class VisualForge:
    """Autonomous asset service (rmart §31).

    `ensure_*` returns existing canonical assets or generates + validates +
    stores missing ones. The caller never cares whether something existed.
    Generators are stubbed/simulated here; a real image-gen backend replaces
    `_generate_candidates` later. This is CPU-side and requires no external call.
    """

    def __init__(self, library: AssetLibrary, resolver: AssetResolver | None = None):
        self.library = library
        self.resolver = resolver or AssetResolver(library)
        self.style = StyleProfile(id="RBZ_CINEMATIC_S01")

    def ensure_visual(self, spec: VisualSpec, view: str = "HERO") -> VisualAsset:
        existing = self.library.latest_canonical(spec.entity_id, spec.asset_type, view)
        if existing:
            return existing
        return self._generate(spec, view)

    def _generate(self, spec: VisualSpec, view: str) -> VisualAsset:
        """Simulate generation + QA + canonize (no external image-gen call)."""
        key = f"{spec.asset_type}:{spec.entity_id}:{view}"
        version = self._next_version(spec.entity_id, spec.asset_type, view)
        asset = VisualAsset(
            id=f"{key}:R{version}", asset_type=spec.asset_type,
            entity_id=spec.entity_id, version=version, status="CANDIDATE",
            canonicality="CANONICAL", mechanical_version=spec.mechanical_version,
            identity_version=f"R{version}", prompt_spec_id=spec.spec_id,
            generator_family="mock", generator_version="1.0",
            seed=hash(spec.spec_id) & 0xffff, file_uri=f"r2://{key}/R{version}.png",
            view=view,
            qa_score=0.95, review_status="auto-approved",
        )
        # Canonize immediately (low-risk simulated assets).
        self.library.add(asset)
        return self.library.approve(asset.asset_key())

    def _next_version(self, entity_id: str, asset_type: str, view: str) -> int:
        latest = self.library.latest_canonical(entity_id, asset_type, view)
        return (latest.version + 1) if latest else 1

    def ensure_shot_assets(self, spec_ids: list[VisualSpec]) -> dict:
        """Ensure assets for a list of specs; returns {spec_id: asset_ref}."""
        out = {}
        for spec in spec_ids:
            for view in spec.required_views:
                asset = self.ensure_visual(spec, view=view)
                out[f"{spec.entity_id}:{view}"] = asset.to_dict()
        return out


@dataclass
class ShotAssetBundle:
    """A coherent reference bundle handed to LTX (rmart §16)."""
    shot_id: str
    subjects: dict[str, dict] = field(default_factory=dict)
    environment: dict = field(default_factory=dict)
    effects: dict[str, dict] = field(default_factory=dict)
    canonical_events: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_asset(id: str, asset_type: str, entity_id: str, version: int = 1,
                canonicality: str = "EDITORIAL", view: str = "HERO",
                mechanical_version: str = "", tags: list[str] | None = None,
                uri: str = "") -> VisualAsset:
    return VisualAsset(id=id, asset_type=asset_type, entity_id=entity_id,
                       version=version, canonicality=canonicality, view=view,
                       mechanical_version=mechanical_version,
                       tags=tags or [], file_uri=uri)
