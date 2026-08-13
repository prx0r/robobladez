import unittest
from robobladez.assets import (
    AssetLibrary, VisualAsset, VisualSpec, StyleProfile, AssetResolver, VisualForge,
    ShotAssetBundle, build_asset,
)


class AssetOntologyTests(unittest.TestCase):
    def setUp(self):
        self.lib = AssetLibrary()
        self.forge = VisualForge(self.lib)
        self.spec = VisualSpec(spec_id="vs-boris", entity_id="boris",
                               asset_type="TALISMAN", mechanical_version="R17")

    def test_visual_forge_generates_canonical_pack(self):
        pack = self.forge.ensure_shot_assets([self.spec])
        # 4 required views generated.
        self.assertEqual(len(pack), 4)
        for view in ("HERO", "SIDE", "TOP", "THREE_QUARTER"):
            self.assertIn(f"boris:{view}", pack)

    def test_visual_forge_reuses_no_regeneration(self):
        self.forge.ensure_shot_assets([self.spec])
        before = len(self.lib.all())
        again = self.forge.ensure_visual(self.spec, view="HERO")
        self.assertEqual(again.version, 1)  # reused, not regenerated
        self.assertEqual(len(self.lib.all()), before)

    def test_resolver_returns_canonical_bundle(self):
        self.forge.ensure_shot_assets([self.spec])
        res = AssetResolver(self.lib)
        refs = res.resolve(entity="boris", asset_type="TALISMAN")
        self.assertEqual(len(refs), 4)
        for r in refs:
            self.assertIn("digest", r)
            self.assertIn("asset_key", r)

    def test_asset_key_and_digest(self):
        a = build_asset("a1", "TALISMAN", "boris", version=1, view="HERO",
                        mechanical_version="R17")
        self.assertEqual(a.asset_key(), "TALISMAN:boris:HERO:mech-R17:R1")
        self.assertEqual(len(a.digest()), 20)
        # Mechanical version is part of the canonical digest.
        b = build_asset("a2", "TALISMAN", "boris", version=1, view="HERO",
                        mechanical_version="R18")
        self.assertNotEqual(a.digest(), b.digest())
        # Mechanical version is part of identity (R17/R18 never collide).
        self.assertNotEqual(a.asset_key(), b.asset_key())

    def test_approve_sets_canonical(self):
        a = build_asset("a1", "TALISMAN", "boris", version=1)
        self.lib.add(a)
        self.lib.approve(a.asset_key())
        latest = self.lib.latest_canonical("boris", "TALISMAN")
        self.assertIsNotNone(latest)
        self.assertEqual(latest.canonicality, "CANONICAL")
        self.assertEqual(latest.status, "APPROVED")

    def test_shot_asset_bundle(self):
        b = ShotAssetBundle(shot_id="m1-s1", canonical_events=["event:m1:184"])
        b.subjects["boris"] = {"asset_key": "TALISMAN:boris:HERO:R1"}
        d = b.to_dict()
        self.assertEqual(d["shot_id"], "m1-s1")
        self.assertEqual(d["canonical_events"], ["event:m1:184"])


if __name__ == "__main__":
    unittest.main()
