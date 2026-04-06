import pytest
from django.utils import timezone

from transactions.unit_tests.factories import UserFactory, RoleFactory, UserProfileFactory, UserAuthTokenFactory, \
    UserSessionFactory, TransactionCategoryFactory
from utilities.constants import ROLE_ADMIN, TRANSACTION_TYPE_INCOME, TRANSACTION_TYPE_EXPENSE


@pytest.fixture
def active_user():
    return UserFactory(username="active_user")


@pytest.fixture
def role_admin():
    return RoleFactory(role_code=ROLE_ADMIN, name="Admin")


@pytest.fixture
def active_profile(active_user, role_admin):
    return UserProfileFactory(user=active_user, role=role_admin, is_active=True)


@pytest.fixture
def active_user_token(active_user):
    return UserAuthTokenFactory(user=active_user, token="valid-token")


@pytest.fixture
def active_user_session(active_user, active_user_token):
    return UserSessionFactory(
        user=active_user,
        auth_token=active_user_token,
        session_id="valid-session-id",
        device_token="valid-device-token",
        logged_in=True,
        expiry_at=timezone.now() + timezone.timedelta(hours=8),
    )


@pytest.fixture
def income_category_1():
    return TransactionCategoryFactory(
        name="Salary",
        transaction_type=TRANSACTION_TYPE_INCOME,
        is_active=True,
    )


@pytest.fixture
def income_category_2():
    return TransactionCategoryFactory(
        name="Freelance",
        transaction_type=TRANSACTION_TYPE_INCOME,
        is_active=True,
    )


@pytest.fixture
def expense_category():
    return TransactionCategoryFactory(
        name="Food",
        transaction_type=TRANSACTION_TYPE_EXPENSE,
        is_active=True,
    )