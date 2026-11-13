from instareciprocal.normalizer import normalize_username


def test_normalizes_username():
    assert normalize_username("  @Some.User_12 ") == "some.user_12"


def test_normalizes_profile_url():
    assert normalize_username("https://www.instagram.com/SomeUser/") == "someuser"


def test_rejects_non_instagram_url():
    assert normalize_username("https://example.com/someuser") is None


def test_rejects_invalid_values():
    assert normalize_username(None) is None
    assert normalize_username("this is not a username") is None
    assert normalize_username("instagram.com/") is None
