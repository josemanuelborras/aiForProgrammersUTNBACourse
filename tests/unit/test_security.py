import pytest

from auth_module.security import hash_password, validate_password_strength, verify_password


def test_hash_password_generates_a_random_salt_when_none_given():
    _, salt_a = hash_password("Sup3rSecret")
    _, salt_b = hash_password("Sup3rSecret")
    assert salt_a != salt_b


def test_hash_password_is_deterministic_for_a_given_salt():
    digest_a, salt = hash_password("Sup3rSecret")
    digest_b, _ = hash_password("Sup3rSecret", salt=salt)
    assert digest_a == digest_b


def test_hash_password_rejects_empty_password():
    with pytest.raises(ValueError):
        hash_password("")


def test_verify_password_accepts_matching_password():
    digest, salt = hash_password("Sup3rSecret")
    assert verify_password("Sup3rSecret", digest, salt) is True


def test_verify_password_rejects_wrong_password():
    digest, salt = hash_password("Sup3rSecret")
    assert verify_password("WrongPass1", digest, salt) is False


def test_verify_password_rejects_empty_password():
    digest, salt = hash_password("Sup3rSecret")
    assert verify_password("", digest, salt) is False


@pytest.mark.parametrize(
    "password,expected_violation_count",
    [
        ("short1", 1),  # too short, but has letter+digit
        ("nodigitshere", 1),  # long enough, has letters, missing digit
        ("12345678", 1),  # long enough, digits only, missing letter
        ("ab", 2),  # too short AND missing digit
        ("Sup3rSecret", 0),  # valid
    ],
)
def test_validate_password_strength_counts_violations(password, expected_violation_count):
    assert len(validate_password_strength(password)) == expected_violation_count
