"""Unit tests for the contact_settle repair (contact flicker) and its pure helpers."""

import unittest

from gt.core.motion_eval import checks_biped
from gt.core.motion_eval.repairs import fixes_contact
from gt.core.motion_eval.repairs import registry
from gt.core.motion_eval.repairs import solvers
from gt.core.motion_eval.repairs.scene import RepairScene
from gt.tests.test_core.test_motion_eval_repairs import FRAME_COUNT
from gt.tests.test_core.test_motion_eval_repairs import HIPS
from gt.tests.test_core.test_motion_eval_repairs import FakeKeyHost
from gt.tests.test_core.test_motion_eval_repairs import build_leg_host
from gt.tests.test_core.test_motion_eval_repairs import build_template
from gt.tests.test_core.test_motion_eval_repairs import translation_matrix

FLICKER_START = 10
FLICKER_END = 20


class FakeTimedHost(FakeKeyHost):
    """Fake host that also reports a frame rate and unit size."""

    def get_fps(self):
        """Gets the frame rate.

        Returns:
            float: 30.
        """
        return 30.0

    def get_meters_per_unit(self):
        """Gets the unit size.

        Returns:
            float: Centimeters.
        """
        return 0.01


def build_flicker_host():
    """Builds a still leg whose foot bobs above the contact height every two frames.

    Returns:
        FakeTimedHost: Host.
    """
    leg_host = build_leg_host(hips_step=0.0)
    host = FakeTimedHost(leg_host.parents, leg_host.local_frames)
    for frame in range(FLICKER_START, FLICKER_END + 1):
        lift = 4.5 if (frame // 2) % 2 else 0.0
        host.local_frames[HIPS][frame] = translation_matrix((0.0, 95.0 + lift, 0.0))
    return host


def count_span_crossings(scene):
    """Measures contact crossings of the left foot in the flicker span, like the check.

    Args:
        scene (RepairScene): Scene access.

    Returns:
        int: Crossings.
    """
    data = fixes_contact.build_motion_data(scene)
    weights = checks_biped.compute_contacts(data)["left"]["weights"]
    return fixes_contact.count_crossings(weights[FLICKER_START - 1:FLICKER_END + 2])


def find_flicker(scene):
    """Finds the frames the contact flicker check would flag for the left foot.

    Args:
        scene (RepairScene): Scene access.

    Returns:
        set: Flagged frame indexes (0.4 s window, 3 crossings, the check defaults).
    """
    data = fixes_contact.build_motion_data(scene)
    weights = checks_biped.compute_contacts(data)["left"]["weights"]
    return checks_biped.find_flicker_frames(weights, int(round(0.4 * data.fps)), 3)


class TestContactPlans(unittest.TestCase):
    def test_choose_states_keeps_one_landing(self):
        weights = [0.1, 0.2, 0.0, 0.6, 0.4, 0.9, 1.0, 0.45, 1.0]
        expected = [False, False, False, True, True, True, True, True, True]
        self.assertEqual(expected, solvers.choose_contact_states(weights))
        self.assertEqual([True] * 3, solvers.choose_contact_states([0.0, 0.0, 0.0], "down"))
        with self.assertRaises(ValueError):
            solvers.choose_contact_states([0.5], "sideways")

    def test_settle_offsets(self):
        offsets = solvers.build_settle_offsets([3.0, 0.2, 5.0, 1.0], [True, True, False, False], 0.5, 6.0)
        self.assertEqual([-2.5, 0.0, 1.0, 5.0], offsets)

    def test_extend_down_edges_follows_contact(self):
        weights = [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0]
        positions = [(float(index) * 0.1, 0.0, 0.0) for index in range(7)]
        start, end, states = fixes_contact.extend_down_edges(weights, positions, 3, 3, [True], 10, 1.0)
        self.assertEqual((1, 5), (start, end))
        self.assertEqual([True] * 5, states)
        start, end, _states = fixes_contact.extend_down_edges(weights, positions, 3, 3, [False], 10, 1.0)
        self.assertEqual((3, 3), (start, end))

    def test_registry_puts_contact_settle_first(self):
        self.assertEqual("contact_settle/default", registry.get_ladder("contact_flicker")[0]["key"])
        self.assertEqual(6, registry.get_fix("contact_settle").get_defaults()["blend"])


class TestContactSettle(unittest.TestCase):
    def test_contact_settle_removes_flicker(self):
        host = build_flicker_host()
        scene = RepairScene(host=host, template=build_template())
        self.assertGreaterEqual(count_span_crossings(scene), 4)
        self.assertTrue(find_flicker(scene))
        definition = registry.get_fix("contact_settle")
        result = definition.function(scene, (FLICKER_START, FLICKER_END), [], definition.merge_params({}))
        self.assertEqual(["left"], list(result["plans"]))
        self.assertEqual(set(), find_flicker(RepairScene(host=host, template=build_template())))
        self.assertEqual(FRAME_COUNT, len(host.local_frames[HIPS]))

    def test_contact_settle_needs_a_template(self):
        scene = RepairScene(host=build_flicker_host())
        with self.assertRaises(ValueError):
            registry.get_fix("contact_settle").function(scene, (10, 20), [], {})


if __name__ == "__main__":
    unittest.main()
