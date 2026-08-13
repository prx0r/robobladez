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


class CanonConflictError(ValueError):
    """Raised when two assets claim the same key with different content."""
    pass


@dataclass(frozen=True)
class VisualAsset:
    """A versioned, hash-addressed canonical visual asset.

    `mechanical_version` ties this image to the exact gameplay body/Daimon it
    represents, so we can say "this image shows BORIS_TALISMAN mechanical R17,
    visual R4" (rmart §8). Immutable; status transitions are recorded in
    status_history, never silent overwrites.
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
    file_sha256: str = ""                 # content hash of the binary (rmreview #8)
    status_history: list[str] = field(default_factory=list)
    review_history: list[str] = field(default_factory=list)
    superseded_by: str = ""

    def asset_key(self) -> str:
        """Stable identity: type + entity + view + mechanical + visual version.

        Mechanical version is part of identity so R17 and R18 visuals never
        collide (rmreview #20/#24: `boris:talisman:mechanical-R17:visual-R4`).
        """
        mech = f":mech-{self.mechanical_version}" if self.mechanical_version else ""
        return f"{self.asset_type}:{self.entity_id}:{self.view}{mech}:R{self.version}"

    def manifest_digest(self) -> str:
        """Hash over canonical metadata (what the asset claims to be)."""
        body = {
            "asset_type": self.asset_type, "entity_id": self.entity_id,
            "version": self.version, "view": self.view,
            "canonicality": self.canonicality, "mechanical_version": self.mechanical_version,
            "identity_version": self.identity_version, "file_uri": self.file_uri,
        }
        return hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:20]

    def content_digest(self) -> str:
        """Hash over the actual image bytes (rmreview #8).

        Distinguishes `asset_manifest_digest` (metadata identity) from
        `file_content_digest` (the binary changed). Falls back to manifest
        digest when file bytes aren't available (e.g. mock assets).
        """
        if self.file_sha256:
            return self.file_sha256[:20]
        return self.manifest_digest()

    def digest(self) -> str:
        """Legacy alias -> content digest (canonical pin)."""
        return self.content_digest()

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["asset_key"] = self.asset_key()
        d["manifest_digest"] = self.manifest_digest()
        d["content_digest"] = self.content_digest()
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
        """Insert append-only. Silent conflicts are NOT allowed (rmreview #9):
        same digest -> idempotent success; different digest -> CanonConflictError.
        """
        key = asset.asset_key()
        existing = self._assets.get(key)
        if existing is None:
            self._assets[key] = asset
            return asset
        if existing.digest() == asset.digest():
            return existing  # idempotent
        raise CanonConflictError(
            f"asset {key} conflict: existing digest differs from new asset")

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
            file_sha256=a.file_sha256, status_history=list(a.status_history),
            review_history=list(a.review_history), superseded_by=a.superseded_by,
        )
        approved.status_history.append("approved")
        self._assets[key] = approved
        return approved

    def supersede(self, key: str, replacement_key: str) -> VisualAsset:
        """Mark an asset SUPERSEDED (rmreview #7: no silent overwrite)."""
        a = self._assets[key]
        replaced = VisualAsset(
            id=a.id, asset_type=a.asset_type, entity_id=a.entity_id,
            version=a.version, status="SUPERSEDED", canonicality=a.canonicality,
            identity_version=a.identity_version, mechanical_version=a.mechanical_version,
            prompt_spec_id=a.prompt_spec_id, reference_asset_ids=a.reference_asset_ids,
            generator_family=a.generator_family, generator_version=a.generator_version,
            seed=a.seed, file_uri=a.file_uri, thumbnail_uri=a.thumbnail_uri,
            alpha_uri=a.alpha_uri, depth_uri=a.depth_uri, mask_uri=a.mask_uri,
            view=a.view, created_at=a.created_at, supersedes=a.supersedes,
            qa_score=a.qa_score, review_status=a.review_status, tags=a.tags,
            file_sha256=a.file_sha256, status_history=list(a.status_history),
            review_history=list(a.review_history), superseded_by=replacement_key,
        )
        replaced.status_history.append("superseded")
        self._assets[key] = replaced
        return replaced

    def get(self, key: str) -> VisualAsset | None:
        return self._assets.get(key)

    def latest_canonical(self, entity_id: str, asset_type: str,
                         view: str = "HERO", mechanical_version: str = "",
                         identity_version: str = "") -> VisualAsset | None:
        """Best approved CANONICAL asset, constrained by mechanical/identity version.

        `mechanical_version` is REQUIRED semantics (rmreview P0.5): a body R18
        must never reuse an R17 visual. If mechanical_version given and no exact
        match exists, returns None (caller must generate a new visual evolution).
        """
        best = None
        for a in self._assets.values():
            if (a.entity_id == entity_id and a.asset_type == asset_type
                    and a.view == view and a.canonicality == "CANONICAL"
                    and a.status == "APPROVED"):
                if mechanical_version and a.mechanical_version != mechanical_version:
                    continue  # wrong gameplay version -> cannot reuse
                if identity_version and a.identity_version != identity_version:
                    continue
                if best is None or a.version > best.version:
                    best = a
        return best

    def references_for(self, entity_id: str, view: str | None = None,
                       mechanical_version: str = "") -> list[VisualAsset]:
        """Canonical assets for an entity, optionally version-constrained."""
        return [a for a in self._assets.values()
                if a.entity_id == entity_id and a.canonicality == "CANONICAL"
                and (view is None or a.view == view)
                and (not mechanical_version or a.mechanical_version == mechanical_version)]

    def all(self) -> list[VisualAsset]:
        return list(self._assets.values())


class AssetResolver:
    """Given an EntrySnapshot-like query, return the canonical reference bundle
    (rmart §15 / rmreview P0.6). Resolution is typed AND version-constrained:
    it cannot return an R17 asset when the shot asked for R18.
    """

    def __init__(self, library: AssetLibrary):
        self.library = library

    def resolve(self, *, entity: str, asset_type: str = "TALISMAN",
                mechanical_version: str = "", daimon_stage: str = "",
                ability: str = "", arena: str = "") -> list[dict]:
        refs = []
        for asset in self.library.references_for(
                entity, mechanical_version=mechanical_version):
            refs.append(self._ref(asset))
        if arena:
            for asset in self.library.references_for(arena):
                refs.append(self._ref(asset))
        if ability:
            for asset in self.library.references_for(ability):
                refs.append(self._ref(asset))
        return refs

    def _ref(self, asset) -> dict:
        return {"type": asset.asset_type, "view": asset.view,
                "asset_key": asset.asset_key(), "uri": asset.file_uri,
                "mechanical_version": asset.mechanical_version,
                "digest": asset.digest()}


class VisualForge:
    """Autonomous asset service (rmart §31) — backend=mock.

    `ensure_*` returns existing canonical assets or generates + validates +
    stores missing ones. The caller never cares whether something existed.
    This is a MOCK backend for CPU contract testing (rmreview #10): generation,
    validation, and canonization are simulated. A real image-gen backend
    replaces `_generate_candidates` later; the interface stays the same.
    """

    def __init__(self, library: AssetLibrary, resolver: AssetResolver | None = None):
        self.library = library
        self.resolver = resolver or AssetResolver(library)
        self.style = StyleProfile(id="RBZ_CINEMATIC_S01")

    def ensure_visual(self, spec: VisualSpec, view: str = "HERO") -> VisualAsset:
        # mechanical_version-aware reuse (rmreview P0.5): R18 must never reuse R17.
        existing = self.library.latest_canonical(
            spec.entity_id, spec.asset_type, view,
            mechanical_version=spec.mechanical_version)
        if existing:
            return existing
        return self._generate(spec, view)

    def _generate(self, spec: VisualSpec, view: str) -> VisualAsset:
        """Simulate generation + QA + canonize (no external image-gen call)."""
        key = f"{spec.asset_type}:{spec.entity_id}:{view}"
        version = self._next_version(spec.entity_id, spec.asset_type, view,
                                     spec.mechanical_version)
        asset = VisualAsset(
            id=f"{key}:R{version}", asset_type=spec.asset_type,
            entity_id=spec.entity_id, version=version, status="CANDIDATE",
            canonicality="CANONICAL", mechanical_version=spec.mechanical_version,
            identity_version=f"R{version}", prompt_spec_id=spec.spec_id,
            generator_family="mock", generator_version="1.0",
            seed=hash(f"{spec.spec_id}:{view}") & 0xffff,
            file_uri=f"r2://{key}/R{version}.png",
            view=view,
            qa_score=0.0, review_status="unvalidated",
            status_history=["candidate"],
        )
        # Canonize immediately (low-risk mock). Real backend runs candidate QA here.
        self.library.add(asset)
        approved = self.library.approve(asset.asset_key())
        approved = VisualAsset(
            id=approved.id, asset_type=approved.asset_type,
            entity_id=approved.entity_id, version=approved.version,
            status="APPROVED", canonicality="CANONICAL",
            identity_version=approved.identity_version,
            mechanical_version=approved.mechanical_version,
            prompt_spec_id=approved.prompt_spec_id,
            reference_asset_ids=approved.reference_asset_ids,
            generator_family=approved.generator_family,
            generator_version=approved.generator_version, seed=approved.seed,
            file_uri=approved.file_uri, thumbnail_uri=approved.thumbnail_uri,
            alpha_uri=approved.alpha_uri, depth_uri=approved.depth_uri,
            mask_uri=approved.mask_uri, view=approved.view,
            created_at=approved.created_at, supersedes=approved.supersedes,
            qa_score=0.95, review_status="mock-auto-approved",
            tags=approved.tags, file_sha256=approved.file_sha256,
            status_history=["candidate", "approved"],
            review_history=["mock-auto-approved"],
            superseded_by=approved.superseded_by,
        )
        self.library._assets[asset.asset_key()] = approved
        return approved

    def _next_version(self, entity_id: str, asset_type: str, view: str,
                      mechanical_version: str) -> int:
        latest = self.library.latest_canonical(
            entity_id, asset_type, view, mechanical_version=mechanical_version)
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
