from utils import normalize_name

def test_repro_npc_name():
    name = "a Rebel Col unknown"
    normalized = normalize_name(name)
    print(f"Original: '{name}'")
    print(f"Normalized: '{normalized}'")
    
    # Based on the user's issue, "a Rebel Col unknown" should probably be "Rebel Col" or just "Rebel Col"
    # Actually if they want it clean, it should strip articles and 'unknown'
    assert "a " not in normalized
    assert "unknown" not in normalized.lower()
    
    # Test multiple prefixes
    assert normalize_name("the a Rebel Col") == "Rebel Col"
    
    # Test normalization in is_probable_player indirectly (it uses startswith check internally too)
    from utils import is_probable_player
    assert is_probable_player("a Rebel Col unknown") == True # Because it becomes Rebel Col, which has 2 caps
    
if __name__ == "__main__":
    test_repro_npc_name()
