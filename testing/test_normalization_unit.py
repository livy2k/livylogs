from utils import normalize_name, is_probable_player, resolve_cooldown_target

def test_normalization():
    # Test normalization
    assert normalize_name("Livy Melee") == "Livy"
    assert normalize_name("Rehote Ranged") == "Rehote"
    assert normalize_name("Damage You") == "You"
    assert normalize_name("  SomeName  ") == "SomeName"
    
    # Test player heuristics
    bosses = ["the krayt dragon", "acklay"]
    assert is_probable_player("Livy", bosses) == True
    assert is_probable_player("Livy Cee", bosses) == True
    assert is_probable_player("a SpecForce marine", bosses) == False
    assert is_probable_player("the Krayt Dragon", bosses) == False
    assert is_probable_player("SpecForce marine", bosses) == False
    assert is_probable_player("You", bosses) == True

    # Cooldown target direction: self-cast intimidate should not land on You
    assert resolve_cooldown_target(
        target="You",
        source="You",
        status_text="You intimidate A Gundark",
        char_name_curr="Autobahn"
    ) == "Gundark"

    # If ambiguous and still self/self for intimidate, drop it instead of mislabeling as You
    assert resolve_cooldown_target(
        target="You",
        source="You",
        status_text="intimidated",
        char_name_curr="Autobahn"
    ) == "Unknown"

    # Victim-forward intimidate combat text should map cooldown to victim, not You
    assert resolve_cooldown_target(
        target="You",
        source="IiIiIiIi",
        status_text="IiIiIiIi looks very intimidated by you!",
        char_name_curr="Autobahn"
    ) == "IiIiIiIi"

    # Same victim-forward text with combat/timestamp prefix should still resolve to victim
    assert resolve_cooldown_target(
        target="You",
        source="IiIiIiIi",
        status_text="[Combat] 19:47:42 IiIiIiIi looks very intimidated by you!",
        char_name_curr="Autobahn"
    ) == "IiIiIiIi"
    
    print("All tests passed!")

if __name__ == "__main__":
    test_normalization()
