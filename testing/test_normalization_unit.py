from utils import normalize_name, is_probable_player

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
    
    print("All tests passed!")

if __name__ == "__main__":
    test_normalization()
