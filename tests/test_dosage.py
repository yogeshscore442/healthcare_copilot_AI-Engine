"""
test_dosage.py — Unit tests for dosage.py schedule parser.
Run: pytest tests/test_dosage.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_engine.dosage import parse_schedule


class TestDashPattern:
    def test_1_0_1(self):
        slots, food, dur = parse_schedule("1-0-1")
        assert set(slots) == {"morning", "night"}
        assert food is None
        assert dur is None

    def test_1_1_1(self):
        slots, food, dur = parse_schedule("1-1-1")
        assert set(slots) == {"morning", "afternoon", "night"}

    def test_0_0_1(self):
        slots, food, dur = parse_schedule("0-0-1")
        assert slots == ["night"]

    def test_1_0_0(self):
        slots, food, dur = parse_schedule("1-0-0")
        assert slots == ["morning"]

    def test_0_1_0(self):
        slots, food, dur = parse_schedule("0-1-0")
        assert slots == ["afternoon"]


class TestAbbreviations:
    def test_od(self):
        slots, food, dur = parse_schedule("OD")
        assert slots == ["morning"]

    def test_bd(self):
        slots, food, dur = parse_schedule("BD")
        assert set(slots) == {"morning", "night"}

    def test_tds(self):
        slots, food, dur = parse_schedule("TDS")
        assert set(slots) == {"morning", "afternoon", "night"}

    def test_tds_lowercase(self):
        slots, food, dur = parse_schedule("tds")
        assert set(slots) == {"morning", "afternoon", "night"}

    def test_hs(self):
        slots, food, dur = parse_schedule("HS")
        assert slots == ["night"]

    def test_sos(self):
        slots, food, dur = parse_schedule("SOS")
        assert slots == []

    def test_qid(self):
        slots, food, dur = parse_schedule("QID")
        assert set(slots) == {"morning", "afternoon", "night"}

    def test_nocte(self):
        slots, food, dur = parse_schedule("Nocte")
        assert slots == ["night"]

    def test_mane(self):
        slots, food, dur = parse_schedule("Mane")
        assert slots == ["morning"]


class TestFoodInstruction:
    def test_after_food(self):
        _, food, _ = parse_schedule("1-0-1 after food")
        assert food == "after_food"

    def test_before_food(self):
        _, food, _ = parse_schedule("OD before food")
        assert food == "before_food"

    def test_ac(self):
        _, food, _ = parse_schedule("TDS AC")
        assert food == "before_food"

    def test_pc(self):
        _, food, _ = parse_schedule("BD PC")
        assert food == "after_food"

    def test_empty_stomach(self):
        _, food, _ = parse_schedule("OD empty stomach")
        assert food == "before_food"

    def test_with_food(self):
        _, food, _ = parse_schedule("1-1-1 with food")
        assert food == "after_food"

    def test_no_food_instruction(self):
        _, food, _ = parse_schedule("BD")
        assert food is None


class TestDuration:
    def test_x_5_days(self):
        _, _, dur = parse_schedule("1-0-1 x 5 days")
        assert dur == 5

    def test_for_7_days(self):
        _, _, dur = parse_schedule("OD for 7 days")
        assert dur == 7

    def test_10d(self):
        _, _, dur = parse_schedule("TDS x 10d")
        assert dur == 10

    def test_no_duration(self):
        _, _, dur = parse_schedule("BD after food")
        assert dur is None


class TestCombined:
    def test_full_string(self):
        slots, food, dur = parse_schedule("1-0-1 after food x 5 days")
        assert set(slots) == {"morning", "night"}
        assert food == "after_food"
        assert dur == 5

    def test_tds_ac_30_days(self):
        slots, food, dur = parse_schedule("TDS AC x 30 days")
        assert set(slots) == {"morning", "afternoon", "night"}
        assert food == "before_food"
        assert dur == 30


class TestEdgeCases:
    def test_none_input(self):
        slots, food, dur = parse_schedule(None)
        assert slots == []
        assert food is None
        assert dur is None

    def test_empty_string(self):
        slots, food, dur = parse_schedule("")
        assert slots == []

    def test_random_string(self):
        slots, food, dur = parse_schedule("apply topically twice daily")
        # No recognizable pattern → empty slots
        assert isinstance(slots, list)
