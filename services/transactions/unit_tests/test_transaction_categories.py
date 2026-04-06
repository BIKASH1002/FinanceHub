'''
Transaction Category

This segment implements unit test for following function defined in transactions/helpers.py:

1) get_transaction_categories
'''

import pytest
from transactions.helpers import get_transaction_categories


@pytest.mark.django_db
class TestGetTransactionCategories:

    def test_get_transaction_categories_success_with_transaction_type(
        self,
        active_user,
        active_profile,
        active_user_token,
        active_user_session,
        income_category_1,
        income_category_2,
        expense_category,
        mocker
    ):
        mocker.patch("transactions.helpers.logger")

        payload = {
            "loggedin_username": active_user.username,
            "auth_token": active_user_token.token,
            "session_id": active_user_session.session_id,
            "device_token": active_user_session.device_token,
            "transaction_type": "income",
        }

        res = get_transaction_categories(payload)

        assert res["success"] is True
        assert "categories_info" in res["data"]
        assert len(res["data"]["categories_info"]) == 2

        category_names = [x["name"] for x in res["data"]["categories_info"]]
        assert "Salary" in category_names
        assert "Freelance" in category_names

        for category in res["data"]["categories_info"]:
            assert category["transaction_type"] == "income"

    def test_get_transaction_categories_success_without_transaction_type(
        self,
        active_user,
        active_profile,
        active_user_token,
        active_user_session,
        income_category_1,
        income_category_2,
        expense_category,
        mocker
    ):
        mocker.patch("transactions.helpers.logger")

        payload = {
            "loggedin_username": active_user.username,
            "auth_token": active_user_token.token,
            "session_id": active_user_session.session_id,
            "device_token": active_user_session.device_token,
        }

        res = get_transaction_categories(payload)

        assert res["success"] is True
        assert "categories_info" in res["data"]
        assert len(res["data"]["categories_info"]) == 3

    def test_get_transaction_categories_fails_for_invalid_transaction_type(
        self,
        active_user,
        active_profile,
        active_user_token,
        active_user_session,
        mocker
    ):
        mocker.patch("transactions.helpers.logger")

        payload = {
            "loggedin_username": active_user.username,
            "auth_token": active_user_token.token,
            "session_id": active_user_session.session_id,
            "device_token": active_user_session.device_token,
            "transaction_type": "invalid_type",
        }

        res = get_transaction_categories(payload)

        assert res["success"] is False
        assert res["error_code"] == 200406
        assert "Invalid transaction type." in res["errors"]

    def test_get_transaction_categories_fails_for_invalid_session(
        self,
        active_user,
        active_profile,
        active_user_token,
        mocker
    ):
        mocker.patch("transactions.helpers.logger")

        payload = {
            "loggedin_username": active_user.username,
            "auth_token": active_user_token.token,
            "session_id": "wrong-session-id",
            "device_token": "wrong-device-token",
        }

        res = get_transaction_categories(payload)

        assert res["success"] is False
        assert res["error_code"] == 100415
        assert "Invalid session." in res["errors"]