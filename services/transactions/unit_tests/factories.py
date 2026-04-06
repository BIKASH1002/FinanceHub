import factory
from django.contrib.auth.models import User
from django.utils import timezone
from factory.django import DjangoModelFactory

from users.models import Role, UserProfile, UserAuthToken, UserSession
from transactions.models import TransactionCategory
from utilities.constants import ROLE_ADMIN, ROLE_ANALYST, ROLE_CLIENT, TRANSACTION_TYPE_INCOME, \
    TRANSACTION_TYPE_EXPENSE


class UserFactory(DjangoModelFactory):

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    first_name = "Test"
    last_name = "User"
    is_active = True


class RoleFactory(DjangoModelFactory):

    class Meta:
        model = Role

    name = factory.Sequence(lambda n: f"Role {n}")
    role_code = factory.Sequence(lambda n: f"role{n}")
    is_active = True


class UserProfileFactory(DjangoModelFactory):

    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    role = factory.SubFactory(RoleFactory)
    first_name = "Test"
    middle_name = ""
    last_name = "User"
    phone_number = "9876543210"
    email_verified = True
    phone_verified = False
    is_active = True


class UserAuthTokenFactory(DjangoModelFactory):

    class Meta:
        model = UserAuthToken

    user = factory.SubFactory(UserFactory)
    token = factory.Sequence(lambda n: f"token-{n}")
    is_active = True
    expires_at = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(hours=24))


class UserSessionFactory(DjangoModelFactory):

    class Meta:
        model = UserSession

    user = factory.SubFactory(UserFactory)
    auth_token = factory.SubFactory(UserAuthTokenFactory, user=factory.SelfAttribute("..user"))
    session_id = factory.Sequence(lambda n: f"session-{n}")
    device_token = factory.Sequence(lambda n: f"device-token-{n}")
    device_ip = "127.0.0.1"
    device_info = "pytest-device"
    logged_in = True
    logged_in_at = factory.LazyFunction(timezone.now)
    expiry_at = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(hours=8))
    refresh_at = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(hours=1))


class TransactionCategoryFactory(DjangoModelFactory):

    class Meta:
        model = TransactionCategory

    name = factory.Sequence(lambda n: f"Category {n}")
    description = "Test category"
    transaction_type = TRANSACTION_TYPE_INCOME
    is_active = True