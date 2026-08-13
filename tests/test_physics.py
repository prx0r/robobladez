import unittest
from robobladez.model import BladeSpec,ArenaSpec
from robobladez.policy import PassivePolicy
from robobladez.engine import run_round

class PhysicsTests(unittest.TestCase):
    def test_passive_energy_does_not_increase(self):
        a=BladeSpec("a"); b=BladeSpec("b")
        ar=ArenaSpec(max_seconds=2.0)
        r=run_round(1,42,ar,a,b,PassivePolicy(),PassivePolicy(),())
        first,last=r.frames[0].states,r.frames[-1].states
        def E(s,spec):
            v2=s["vel"]["x"]**2+s["vel"]["y"]**2
            return .5*spec.mass*v2+.5*spec.inertia*s["omega"]**2
        self.assertLessEqual(E(last["a"],a)+E(last["b"],b),
                             (E(first["a"],a)+E(first["b"],b))*(1+1e-9))

    def test_spin_decays_passively(self):
        a=BladeSpec("a"); b=BladeSpec("b")
        r=run_round(1,9,ArenaSpec(max_seconds=.5),a,b,PassivePolicy(),PassivePolicy(),())
        self.assertLess(abs(r.frames[-1].states["a"]["omega"]),
                        abs(r.frames[0].states["a"]["omega"]))

if __name__=="__main__":
    unittest.main()
