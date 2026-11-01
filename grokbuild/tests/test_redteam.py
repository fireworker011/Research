from grokbuild.qa.inspectors import inspector_3, inspector_6
from grokbuild.qa.redteam import cases


def test_seven_attacks_are_all_blocked():
    attacks = cases()
    assert tuple(attack.case_id for attack in attacks) == (1, 2, 3, 4, 5, 6, 7)
    assert all(inspector_6(attack.image, fixes_used=0) is False for attack in attacks)


def test_finger_attack_is_an_anatomy_failure():
    finger_attack = cases()[5]
    assert finger_attack.case_id == 6
    assert inspector_3(finger_attack.image.anatomy) is False
