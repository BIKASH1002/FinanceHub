import logging
from decimal import Decimal, InvalidOperation
from datetime import datetime

from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone

from utilities.utils import get_response_format
from utilities.constants import ROLE_ADMIN, ROLE_ANALYST, ROLE_CLIENT, TRANSACTION_TYPE_INCOME, \
    TRANSACTION_TYPE_EXPENSE, TRANSACTION_AUDIT_ACTION_CREATE, TRANSACTION_AUDIT_ACTION_UPDATE, \
    TRANSACTION_AUDIT_ACTION_DELETE

from services.users.models import UserAuthToken, UserSession, UserProfile
from .models import TransactionCategory, Transaction, TransactionAuditLog

logger = logging.getLogger(__name__)


def create_transaction_category(category_info):
    response = get_response_format()

    loggedin_user_obj = None
    loggedin_auth_token_obj = None
    loggedin_session_obj = None
    loggedin_profile_obj = None
    category_obj = None
    existing_category_obj = None

    if category_info["loggedin_username"] and category_info["auth_token"] and \
       category_info["session_id"] and category_info["device_token"] and \
       category_info["name"] and category_info["transaction_type"]:

        try:
            loggedin_user_obj = User.objects.get(
                username=category_info["loggedin_username"],
                is_active=True
            )
        except Exception as e:
            logger.error("Logged in user not found.", str(e))

        if loggedin_user_obj:
            try:
                loggedin_auth_token_obj = UserAuthToken.objects.get(
                    user=loggedin_user_obj,
                    token=category_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Logged in user auth token not found.", str(e))

            if loggedin_auth_token_obj:
                try:
                    loggedin_session_obj = UserSession.objects.get(
                        user=loggedin_user_obj,
                        auth_token=loggedin_auth_token_obj,
                        session_id=category_info["session_id"],
                        device_token=category_info["device_token"],
                        logged_in=True
                    )
                except Exception as e:
                    logger.error("Logged in user session not found.", str(e))

                if loggedin_session_obj:
                    if timezone.now() > loggedin_session_obj.expiry_at:
                        response["success"] = False
                        response["errors"].append("Session expired.")
                        response["error_code"] = 100414
                    else:
                        try:
                            loggedin_profile_obj = UserProfile.objects.get(
                                user=loggedin_user_obj,
                                is_active=True
                            )
                        except Exception as e:
                            logger.error("Logged in user profile not found.", str(e))

                        if loggedin_profile_obj:
                            if loggedin_profile_obj.role.role_code == ROLE_ADMIN:
                                if category_info["transaction_type"] in [TRANSACTION_TYPE_INCOME, TRANSACTION_TYPE_EXPENSE]:
                                    try:
                                        existing_category_obj = TransactionCategory.objects.get(
                                            name__iexact=category_info["name"].strip(),
                                            transaction_type=category_info["transaction_type"],
                                            is_active=True
                                        )
                                    except Exception as e:
                                        logger.info("Transaction category not found.", str(e))

                                    if existing_category_obj:
                                        response["success"] = False
                                        response["errors"].append("Transaction category already exists.")
                                        response["error_code"] = 200402
                                    else:
                                        try:
                                            category_obj = TransactionCategory(
                                                name=category_info["name"].strip(),
                                                description=category_info["description"],
                                                transaction_type=category_info["transaction_type"],
                                                is_active=True,
                                                created_by=loggedin_user_obj,
                                                updated_by=loggedin_user_obj
                                            )
                                            category_obj.save()
                                        except Exception as e:
                                            logger.error("Transaction category save failed.", str(e), category_info)

                                        if category_obj:
                                            response["success"] = True
                                            response["data"]["category_info"] = {
                                                "category_id": category_obj.id,
                                                "name": category_obj.name,
                                                "description": category_obj.description,
                                                "transaction_type": category_obj.transaction_type,
                                                "is_active": category_obj.is_active,
                                                "created_at": category_obj.created_at,
                                            }
                                        else:
                                            response["success"] = False
                                            response["errors"].append("Transaction category not created.")
                                            response["error_code"] = 200405
                                else:
                                    response["success"] = False
                                    response["errors"].append("Invalid transaction type.")
                                    response["error_code"] = 200406
                            else:
                                response["success"] = False
                                response["errors"].append("User not authorized to create transaction category.")
                                response["error_code"] = 100416
                        else:
                            response["success"] = False
                            response["errors"].append("User profile not found.")
                            response["error_code"] = 100420
                else:
                    response["success"] = False
                    response["errors"].append("Invalid session.")
                    response["error_code"] = 100415
            else:
                response["success"] = False
                response["errors"].append("Invalid token.")
                response["error_code"] = 100412
        else:
            response["success"] = False
            response["errors"].append("User not found.")
            response["error_code"] = 100404
    else:
        response["success"] = False
        response["errors"].append("Invalid input, required fields not provided.")
        response["error_code"] = 100401

    return response


def update_transaction_category(category_info):
    response = get_response_format()

    loggedin_user_obj = None
    loggedin_auth_token_obj = None
    loggedin_session_obj = None
    loggedin_profile_obj = None
    category_obj = None
    duplicate_category_obj = None

    if category_info["loggedin_username"] and category_info["auth_token"] and \
       category_info["session_id"] and category_info["device_token"] and \
       category_info["category_id"]:

        try:
            loggedin_user_obj = User.objects.get(
                username=category_info["loggedin_username"],
                is_active=True
            )
        except Exception as e:
            logger.error("Logged in user not found.", str(e))

        if loggedin_user_obj:
            try:
                loggedin_auth_token_obj = UserAuthToken.objects.get(
                    user=loggedin_user_obj,
                    token=category_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Logged in user auth token not found.", str(e))

            if loggedin_auth_token_obj:
                try:
                    loggedin_session_obj = UserSession.objects.get(
                        user=loggedin_user_obj,
                        auth_token=loggedin_auth_token_obj,
                        session_id=category_info["session_id"],
                        device_token=category_info["device_token"],
                        logged_in=True
                    )
                except Exception as e:
                    logger.error("Logged in user session not found.", str(e))

                if loggedin_session_obj:
                    if timezone.now() > loggedin_session_obj.expiry_at:
                        response["success"] = False
                        response["errors"].append("Session expired.")
                        response["error_code"] = 100414
                    else:
                        try:
                            loggedin_profile_obj = UserProfile.objects.get(
                                user=loggedin_user_obj,
                                is_active=True
                            )
                        except Exception as e:
                            logger.error("Logged in user profile not found.", str(e))

                        if loggedin_profile_obj:
                            if loggedin_profile_obj.role.role_code == ROLE_ADMIN:
                                try:
                                    category_obj = TransactionCategory.objects.get(
                                        id=category_info["category_id"]
                                    )
                                except Exception as e:
                                    logger.error("Transaction category not found.", str(e))

                                if category_obj:
                                    updated_name = category_obj.name
                                    updated_description = category_obj.description
                                    updated_transaction_type = category_obj.transaction_type
                                    updated_is_active = category_obj.is_active

                                    if category_info["name"] is not None:
                                        updated_name = category_info["name"].strip()

                                    if category_info["description"] is not None:
                                        updated_description = category_info["description"]

                                    if category_info["transaction_type"] is not None:
                                        if category_info["transaction_type"] in [TRANSACTION_TYPE_INCOME, TRANSACTION_TYPE_EXPENSE]:
                                            updated_transaction_type = category_info["transaction_type"]
                                        else:
                                            response["success"] = False
                                            response["errors"].append("Invalid transaction type.")
                                            response["error_code"] = 200406

                                    if category_info["is_active"] is not None:
                                        updated_is_active = bool(category_info["is_active"])

                                    if len(response["errors"]) == 0:
                                        try:
                                            duplicate_category_obj = TransactionCategory.objects.get(
                                                name__iexact=updated_name,
                                                transaction_type=updated_transaction_type
                                            )
                                        except Exception as e:
                                            logger.info("Duplicate transaction category not found.", str(e))

                                        if duplicate_category_obj and duplicate_category_obj.id != category_obj.id:
                                            response["success"] = False
                                            response["errors"].append("Transaction category with same name and type already exists.")
                                            response["error_code"] = 200407
                                        else:
                                            try:
                                                category_obj.name = updated_name
                                                category_obj.description = updated_description
                                                category_obj.transaction_type = updated_transaction_type
                                                category_obj.is_active = updated_is_active
                                                category_obj.updated_by = loggedin_user_obj
                                                category_obj.save()
                                            except Exception as e:
                                                logger.error("Transaction category update failed.", str(e), category_info)

                                            response["success"] = True
                                            response["data"]["category_info"] = {
                                                "category_id": category_obj.id,
                                                "name": category_obj.name,
                                                "description": category_obj.description,
                                                "transaction_type": category_obj.transaction_type,
                                                "is_active": category_obj.is_active,
                                                "updated_at": category_obj.updated_at,
                                            }
                                else:
                                    response["success"] = False
                                    response["errors"].append("Transaction category not found.")
                                    response["error_code"] = 200404
                            else:
                                response["success"] = False
                                response["errors"].append("User not authorized to update transaction category.")
                                response["error_code"] = 100416
                        else:
                            response["success"] = False
                            response["errors"].append("User profile not found.")
                            response["error_code"] = 100420
                else:
                    response["success"] = False
                    response["errors"].append("Invalid session.")
                    response["error_code"] = 100415
            else:
                response["success"] = False
                response["errors"].append("Invalid token.")
                response["error_code"] = 100412
        else:
            response["success"] = False
            response["errors"].append("User not found.")
            response["error_code"] = 100404
    else:
        response["success"] = False
        response["errors"].append("Invalid input, required fields not provided.")
        response["error_code"] = 100401

    return response


def get_transaction_categories(category_info):
    response = get_response_format()

    loggedin_user_obj = None
    loggedin_auth_token_obj = None
    loggedin_session_obj = None
    loggedin_profile_obj = None
    category_queryset = None
    category_list = []

    if category_info["loggedin_username"] and category_info["auth_token"] and \
       category_info["session_id"] and category_info["device_token"]:

        try:
            loggedin_user_obj = User.objects.get(
                username=category_info["loggedin_username"],
                is_active=True
            )
        except Exception as e:
            logger.error("Logged in user not found.", str(e))

        if loggedin_user_obj:
            try:
                loggedin_auth_token_obj = UserAuthToken.objects.get(
                    user=loggedin_user_obj,
                    token=category_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Logged in user auth token not found.", str(e))

            if loggedin_auth_token_obj:
                try:
                    loggedin_session_obj = UserSession.objects.get(
                        user=loggedin_user_obj,
                        auth_token=loggedin_auth_token_obj,
                        session_id=category_info["session_id"],
                        device_token=category_info["device_token"],
                        logged_in=True
                    )
                except Exception as e:
                    logger.error("Logged in user session not found.", str(e))

                if loggedin_session_obj:
                    if timezone.now() > loggedin_session_obj.expiry_at:
                        response["success"] = False
                        response["errors"].append("Session expired.")
                        response["error_code"] = 100414
                    else:
                        try:
                            loggedin_profile_obj = UserProfile.objects.get(
                                user=loggedin_user_obj,
                                is_active=True
                            )
                        except Exception as e:
                            logger.error("Logged in user profile not found.", str(e))

                        if loggedin_profile_obj:
                            if loggedin_profile_obj.role.role_code in [ROLE_ADMIN, ROLE_ANALYST, ROLE_CLIENT]:
                                try:
                                    category_queryset = TransactionCategory.objects.filter(
                                        is_active=True
                                    ).order_by("id")
                                except Exception as e:
                                    logger.error("Transaction category list fetch failed.", str(e))

                                if category_queryset is not None:
                                    if category_info["transaction_type"]:
                                        if category_info["transaction_type"] in [TRANSACTION_TYPE_INCOME, TRANSACTION_TYPE_EXPENSE]:
                                            category_queryset = category_queryset.filter(
                                                transaction_type=category_info["transaction_type"]
                                            )
                                        else:
                                            response["success"] = False
                                            response["errors"].append("Invalid transaction type.")
                                            response["error_code"] = 200406

                                    if len(response["errors"]) == 0:
                                        try:
                                            category_list = [{
                                                "category_id": x.id,
                                                "name": x.name,
                                                "description": x.description,
                                                "transaction_type": x.transaction_type,
                                                "is_active": x.is_active,
                                                "created_at": x.created_at,
                                            } for x in category_queryset]
                                        except Exception as e:
                                            logger.error("Transaction category list formatting failed.", str(e))

                                        response["success"] = True
                                        response["data"]["categories_info"] = category_list
                                else:
                                    response["success"] = False
                                    response["errors"].append("Transaction categories not found.")
                                    response["error_code"] = 200408
                            else:
                                response["success"] = False
                                response["errors"].append("User not authorized to access transaction categories.")
                                response["error_code"] = 100416
                        else:
                            response["success"] = False
                            response["errors"].append("User profile not found.")
                            response["error_code"] = 100420
                else:
                    response["success"] = False
                    response["errors"].append("Invalid session.")
                    response["error_code"] = 100415
            else:
                response["success"] = False
                response["errors"].append("Invalid token.")
                response["error_code"] = 100412
        else:
            response["success"] = False
            response["errors"].append("User not found.")
            response["error_code"] = 100404
    else:
        response["success"] = False
        response["errors"].append("Invalid input, required fields not provided.")
        response["error_code"] = 100401

    return response


def create_transaction_record(transaction_info):
    response = get_response_format()

    loggedin_user_obj = None
    loggedin_auth_token_obj = None
    loggedin_session_obj = None
    loggedin_profile_obj = None
    category_obj = None
    transaction_obj = None
    audit_log_obj = None
    parsed_amount = None
    parsed_transaction_date = None

    if transaction_info["loggedin_username"] and transaction_info["auth_token"] and \
       transaction_info["session_id"] and transaction_info["device_token"] and \
       transaction_info["title"] and transaction_info["amount"] is not None and \
       transaction_info["transaction_type"] and transaction_info["category_id"] and \
       transaction_info["transaction_date"]:

        try:
            loggedin_user_obj = User.objects.get(
                username=transaction_info["loggedin_username"],
                is_active=True
            )
        except Exception as e:
            logger.error("Logged in user not found.", str(e))

        if loggedin_user_obj:
            try:
                loggedin_auth_token_obj = UserAuthToken.objects.get(
                    user=loggedin_user_obj,
                    token=transaction_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Logged in user auth token not found.", str(e))

            if loggedin_auth_token_obj:
                try:
                    loggedin_session_obj = UserSession.objects.get(
                        user=loggedin_user_obj,
                        auth_token=loggedin_auth_token_obj,
                        session_id=transaction_info["session_id"],
                        device_token=transaction_info["device_token"],
                        logged_in=True
                    )
                except Exception as e:
                    logger.error("Logged in user session not found.", str(e))

                if loggedin_session_obj:
                    if timezone.now() > loggedin_session_obj.expiry_at:
                        response["success"] = False
                        response["errors"].append("Session expired.")
                        response["error_code"] = 100414
                    else:
                        try:
                            loggedin_profile_obj = UserProfile.objects.get(
                                user=loggedin_user_obj,
                                is_active=True
                            )
                        except Exception as e:
                            logger.error("Logged in user profile not found.", str(e))

                        if loggedin_profile_obj:
                            if loggedin_profile_obj.role.role_code == ROLE_ADMIN:
                                if transaction_info["transaction_type"] in [TRANSACTION_TYPE_INCOME, TRANSACTION_TYPE_EXPENSE]:
                                    try:
                                        parsed_amount = Decimal(str(transaction_info["amount"]))
                                    except (InvalidOperation, ValueError, TypeError) as e:
                                        logger.error("Invalid transaction amount.", str(e))

                                    try:
                                        parsed_transaction_date = datetime.strptime(
                                            transaction_info["transaction_date"], "%Y-%m-%d"
                                        ).date()
                                    except Exception as e:
                                        logger.error("Invalid transaction date format.", str(e))

                                    if parsed_amount is None:
                                        response["success"] = False
                                        response["errors"].append("Invalid transaction amount.")
                                        response["error_code"] = 200409
                                    elif parsed_amount <= 0:
                                        response["success"] = False
                                        response["errors"].append("Transaction amount must be greater than zero.")
                                        response["error_code"] = 200410
                                    elif not parsed_transaction_date:
                                        response["success"] = False
                                        response["errors"].append("Invalid transaction date. Use YYYY-MM-DD format.")
                                        response["error_code"] = 200411
                                    else:
                                        try:
                                            category_obj = TransactionCategory.objects.get(
                                                id=transaction_info["category_id"],
                                                is_active=True
                                            )
                                        except Exception as e:
                                            logger.error("Transaction category not found.", str(e))

                                        if category_obj:
                                            if category_obj.transaction_type == transaction_info["transaction_type"]:
                                                try:
                                                    transaction_obj = Transaction(
                                                        title=transaction_info["title"].strip(),
                                                        amount=parsed_amount,
                                                        transaction_type=transaction_info["transaction_type"],
                                                        category=category_obj,
                                                        transaction_date=parsed_transaction_date,
                                                        description=transaction_info["description"],
                                                        is_active=True,
                                                        created_by=loggedin_user_obj,
                                                        updated_by=loggedin_user_obj
                                                    )
                                                    transaction_obj.save()
                                                except Exception as e:
                                                    logger.error("Transaction save failed.", str(e), transaction_info)

                                                if transaction_obj:
                                                    try:
                                                        audit_log_obj = TransactionAuditLog(
                                                            transaction=transaction_obj,
                                                            action=TRANSACTION_AUDIT_ACTION_CREATE,
                                                            action_by=loggedin_user_obj,
                                                            remarks="Transaction created."
                                                        )
                                                        audit_log_obj.save()
                                                    except Exception as e:
                                                        logger.error("Transaction audit log save failed.", str(e), transaction_info)

                                                    response["success"] = True
                                                    response["data"]["transaction_info"] = {
                                                        "transaction_id": str(transaction_obj.transaction_id),
                                                        "title": transaction_obj.title,
                                                        "amount": str(transaction_obj.amount),
                                                        "transaction_type": transaction_obj.transaction_type,
                                                        "category_id": transaction_obj.category.id,
                                                        "category_name": transaction_obj.category.name,
                                                        "transaction_date": transaction_obj.transaction_date,
                                                        "description": transaction_obj.description,
                                                        "is_active": transaction_obj.is_active,
                                                        "created_at": transaction_obj.created_at,
                                                    }
                                                else:
                                                    response["success"] = False
                                                    response["errors"].append("Transaction not created.")
                                                    response["error_code"] = 200412
                                            else:
                                                response["success"] = False
                                                response["errors"].append("Category transaction type does not match transaction type.")
                                                response["error_code"] = 200413
                                        else:
                                            response["success"] = False
                                            response["errors"].append("Transaction category not found.")
                                            response["error_code"] = 200404
                                else:
                                    response["success"] = False
                                    response["errors"].append("Invalid transaction type.")
                                    response["error_code"] = 200406
                            else:
                                response["success"] = False
                                response["errors"].append("User not authorized to create transaction.")
                                response["error_code"] = 100416
                        else:
                            response["success"] = False
                            response["errors"].append("User profile not found.")
                            response["error_code"] = 100420
                else:
                    response["success"] = False
                    response["errors"].append("Invalid session.")
                    response["error_code"] = 100415
            else:
                response["success"] = False
                response["errors"].append("Invalid token.")
                response["error_code"] = 100412
        else:
            response["success"] = False
            response["errors"].append("User not found.")
            response["error_code"] = 100404
    else:
        response["success"] = False
        response["errors"].append("Invalid input, required fields not provided.")
        response["error_code"] = 100401

    return response


def update_transaction_record(transaction_info):
    response = get_response_format()

    loggedin_user_obj = None
    loggedin_auth_token_obj = None
    loggedin_session_obj = None
    loggedin_profile_obj = None
    transaction_obj = None
    category_obj = None
    audit_log_obj = None

    if transaction_info["loggedin_username"] and transaction_info["auth_token"] and \
       transaction_info["session_id"] and transaction_info["device_token"] and \
       transaction_info["transaction_id"]:

        try:
            loggedin_user_obj = User.objects.get(
                username=transaction_info["loggedin_username"],
                is_active=True
            )
        except Exception as e:
            logger.error("Logged in user not found.", str(e))

        if loggedin_user_obj:
            try:
                loggedin_auth_token_obj = UserAuthToken.objects.get(
                    user=loggedin_user_obj,
                    token=transaction_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Logged in user auth token not found.", str(e))

            if loggedin_auth_token_obj:
                try:
                    loggedin_session_obj = UserSession.objects.get(
                        user=loggedin_user_obj,
                        auth_token=loggedin_auth_token_obj,
                        session_id=transaction_info["session_id"],
                        device_token=transaction_info["device_token"],
                        logged_in=True
                    )
                except Exception as e:
                    logger.error("Logged in user session not found.", str(e))

                if loggedin_session_obj:
                    if timezone.now() > loggedin_session_obj.expiry_at:
                        response["success"] = False
                        response["errors"].append("Session expired.")
                        response["error_code"] = 100414
                    else:
                        try:
                            loggedin_profile_obj = UserProfile.objects.get(
                                user=loggedin_user_obj,
                                is_active=True
                            )
                        except Exception as e:
                            logger.error("Logged in user profile not found.", str(e))

                        if loggedin_profile_obj:
                            if loggedin_profile_obj.role.role_code == ROLE_ADMIN:
                                try:
                                    transaction_obj = Transaction.objects.select_related("category").get(
                                        transaction_id=transaction_info["transaction_id"],
                                        is_active=True
                                    )
                                except Exception as e:
                                    logger.error("Transaction not found.", str(e))

                                if transaction_obj:
                                    updated_title = transaction_obj.title
                                    updated_amount = transaction_obj.amount
                                    updated_transaction_type = transaction_obj.transaction_type
                                    updated_category_obj = transaction_obj.category
                                    updated_transaction_date = transaction_obj.transaction_date
                                    updated_description = transaction_obj.description

                                    if transaction_info["title"] is not None:
                                        updated_title = transaction_info["title"].strip()

                                    if transaction_info["amount"] is not None:
                                        try:
                                            parsed_amount = Decimal(str(transaction_info["amount"]))
                                        except (InvalidOperation, ValueError, TypeError) as e:
                                            parsed_amount = None
                                            logger.error("Invalid transaction amount.", str(e))

                                        if parsed_amount is None:
                                            response["success"] = False
                                            response["errors"].append("Invalid transaction amount.")
                                            response["error_code"] = 200409
                                        elif parsed_amount <= 0:
                                            response["success"] = False
                                            response["errors"].append("Transaction amount must be greater than zero.")
                                            response["error_code"] = 200410
                                        else:
                                            updated_amount = parsed_amount

                                    if transaction_info["transaction_type"] is not None:
                                        if transaction_info["transaction_type"] in [TRANSACTION_TYPE_INCOME, TRANSACTION_TYPE_EXPENSE]:
                                            updated_transaction_type = transaction_info["transaction_type"]
                                        else:
                                            response["success"] = False
                                            response["errors"].append("Invalid transaction type.")
                                            response["error_code"] = 200406

                                    if transaction_info["category_id"] is not None:
                                        try:
                                            category_obj = TransactionCategory.objects.get(
                                                id=transaction_info["category_id"],
                                                is_active=True
                                            )
                                        except Exception as e:
                                            logger.error("Transaction category not found.", str(e))

                                        if category_obj:
                                            updated_category_obj = category_obj
                                        else:
                                            response["success"] = False
                                            response["errors"].append("Transaction category not found.")
                                            response["error_code"] = 200404

                                    if transaction_info["transaction_date"] is not None:
                                        try:
                                            parsed_transaction_date = datetime.strptime(
                                                transaction_info["transaction_date"], "%Y-%m-%d"
                                            ).date()
                                        except Exception as e:
                                            parsed_transaction_date = None
                                            logger.error("Invalid transaction date format.", str(e))

                                        if parsed_transaction_date:
                                            updated_transaction_date = parsed_transaction_date
                                        else:
                                            response["success"] = False
                                            response["errors"].append("Invalid transaction date. Use YYYY-MM-DD format.")
                                            response["error_code"] = 200411

                                    if transaction_info["description"] is not None:
                                        updated_description = transaction_info["description"]

                                    if len(response["errors"]) == 0:
                                        if updated_category_obj.transaction_type != updated_transaction_type:
                                            response["success"] = False
                                            response["errors"].append("Category transaction type does not match transaction type.")
                                            response["error_code"] = 200413
                                        else:
                                            try:
                                                transaction_obj.title = updated_title
                                                transaction_obj.amount = updated_amount
                                                transaction_obj.transaction_type = updated_transaction_type
                                                transaction_obj.category = updated_category_obj
                                                transaction_obj.transaction_date = updated_transaction_date
                                                transaction_obj.description = updated_description
                                                transaction_obj.updated_by = loggedin_user_obj
                                                transaction_obj.save()
                                            except Exception as e:
                                                logger.error("Transaction update failed.", str(e), transaction_info)

                                            if transaction_obj:
                                                try:
                                                    audit_log_obj = TransactionAuditLog(
                                                        transaction=transaction_obj,
                                                        action=TRANSACTION_AUDIT_ACTION_UPDATE,
                                                        action_by=loggedin_user_obj,
                                                        remarks="Transaction updated."
                                                    )
                                                    audit_log_obj.save()
                                                except Exception as e:
                                                    logger.error("Transaction audit log save failed.", str(e), transaction_info)

                                                response["success"] = True
                                                response["data"]["transaction_info"] = {
                                                    "transaction_id": str(transaction_obj.transaction_id),
                                                    "title": transaction_obj.title,
                                                    "amount": str(transaction_obj.amount),
                                                    "transaction_type": transaction_obj.transaction_type,
                                                    "category_id": transaction_obj.category.id,
                                                    "category_name": transaction_obj.category.name,
                                                    "transaction_date": transaction_obj.transaction_date,
                                                    "description": transaction_obj.description,
                                                    "is_active": transaction_obj.is_active,
                                                    "updated_at": transaction_obj.updated_at,
                                                }
                                            else:
                                                response["success"] = False
                                                response["errors"].append("Transaction not updated.")
                                                response["error_code"] = 200414
                                else:
                                    response["success"] = False
                                    response["errors"].append("Transaction not found.")
                                    response["error_code"] = 200415
                            else:
                                response["success"] = False
                                response["errors"].append("User not authorized to update transaction.")
                                response["error_code"] = 100416
                        else:
                            response["success"] = False
                            response["errors"].append("User profile not found.")
                            response["error_code"] = 100420
                else:
                    response["success"] = False
                    response["errors"].append("Invalid session.")
                    response["error_code"] = 100415
            else:
                response["success"] = False
                response["errors"].append("Invalid token.")
                response["error_code"] = 100412
        else:
            response["success"] = False
            response["errors"].append("User not found.")
            response["error_code"] = 100404
    else:
        response["success"] = False
        response["errors"].append("Invalid input, required fields not provided.")
        response["error_code"] = 100401

    return response


def get_transaction_records(transaction_info):
    response = get_response_format()

    loggedin_user_obj = None
    loggedin_auth_token_obj = None
    loggedin_session_obj = None
    loggedin_profile_obj = None
    transactions_queryset = None
    paginated_transactions = []

    page = 1
    page_size = 10

    if transaction_info["loggedin_username"] and transaction_info["auth_token"] and \
       transaction_info["session_id"] and transaction_info["device_token"]:

        if transaction_info["page"]:
            page = transaction_info["page"]

        if transaction_info["page_size"]:
            page_size = transaction_info["page_size"]

        try:
            loggedin_user_obj = User.objects.get(
                username=transaction_info["loggedin_username"],
                is_active=True
            )
        except Exception as e:
            logger.error("Logged in user not found.", str(e))

        if loggedin_user_obj:
            try:
                loggedin_auth_token_obj = UserAuthToken.objects.get(
                    user=loggedin_user_obj,
                    token=transaction_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Logged in user auth token not found.", str(e))

            if loggedin_auth_token_obj:
                try:
                    loggedin_session_obj = UserSession.objects.get(
                        user=loggedin_user_obj,
                        auth_token=loggedin_auth_token_obj,
                        session_id=transaction_info["session_id"],
                        device_token=transaction_info["device_token"],
                        logged_in=True
                    )
                except Exception as e:
                    logger.error("Logged in user session not found.", str(e))

                if loggedin_session_obj:
                    if timezone.now() > loggedin_session_obj.expiry_at:
                        response["success"] = False
                        response["errors"].append("Session expired.")
                        response["error_code"] = 100414
                    else:
                        try:
                            loggedin_profile_obj = UserProfile.objects.get(
                                user=loggedin_user_obj,
                                is_active=True
                            )
                        except Exception as e:
                            logger.error("Logged in user profile not found.", str(e))

                        if loggedin_profile_obj:
                            if loggedin_profile_obj.role.role_code in [ROLE_ADMIN, ROLE_ANALYST, ROLE_CLIENT]:
                                try:
                                    transactions_queryset = Transaction.objects.select_related(
                                        "category"
                                    ).filter(
                                        is_active=True,
                                        category__is_active=True
                                    ).order_by("-transaction_date", "-id")
                                except Exception as e:
                                    logger.error("Transaction list fetch failed.", str(e))

                                if transactions_queryset is not None:
                                    if transaction_info["transaction_type"]:
                                        if transaction_info["transaction_type"] in [TRANSACTION_TYPE_INCOME, TRANSACTION_TYPE_EXPENSE]:
                                            transactions_queryset = transactions_queryset.filter(
                                                transaction_type=transaction_info["transaction_type"]
                                            )
                                        else:
                                            response["success"] = False
                                            response["errors"].append("Invalid transaction type.")
                                            response["error_code"] = 200406

                                    if transaction_info["category_id"] and len(response["errors"]) == 0:
                                        transactions_queryset = transactions_queryset.filter(
                                            category_id=transaction_info["category_id"]
                                        )

                                    if transaction_info["start_date"] and len(response["errors"]) == 0:
                                        try:
                                            parsed_start_date = datetime.strptime(
                                                transaction_info["start_date"], "%Y-%m-%d"
                                            ).date()
                                        except Exception as e:
                                            parsed_start_date = None
                                            logger.error("Invalid start date format.", str(e))

                                        if parsed_start_date:
                                            transactions_queryset = transactions_queryset.filter(
                                                transaction_date__gte=parsed_start_date
                                            )
                                        else:
                                            response["success"] = False
                                            response["errors"].append("Invalid start date. Use YYYY-MM-DD format.")
                                            response["error_code"] = 200416

                                    if transaction_info["end_date"] and len(response["errors"]) == 0:
                                        try:
                                            parsed_end_date = datetime.strptime(
                                                transaction_info["end_date"], "%Y-%m-%d"
                                            ).date()
                                        except Exception as e:
                                            parsed_end_date = None
                                            logger.error("Invalid end date format.", str(e))

                                        if parsed_end_date:
                                            transactions_queryset = transactions_queryset.filter(
                                                transaction_date__lte=parsed_end_date
                                            )
                                        else:
                                            response["success"] = False
                                            response["errors"].append("Invalid end date. Use YYYY-MM-DD format.")
                                            response["error_code"] = 200417

                                    if transaction_info["search"] and len(response["errors"]) == 0:
                                        transactions_queryset = transactions_queryset.filter(
                                            Q(title__icontains=transaction_info["search"].strip()) |
                                            Q(description__icontains=transaction_info["search"].strip()) |
                                            Q(category__name__icontains=transaction_info["search"].strip())
                                        )

                                    if len(response["errors"]) == 0:
                                        try:
                                            paginator = Paginator(transactions_queryset, page_size)
                                            transactions_page = paginator.page(page)
                                        except PageNotAnInteger:
                                            transactions_page = paginator.page(1)
                                        except EmptyPage:
                                            transactions_page = paginator.page(paginator.num_pages)
                                        except Exception as e:
                                            transactions_page = None
                                            logger.error("Transaction pagination failed.", str(e))

                                        if transactions_page:
                                            try:
                                                paginated_transactions = [{
                                                    "transaction_id": str(x.transaction_id),
                                                    "title": x.title,
                                                    "amount": str(x.amount),
                                                    "transaction_type": x.transaction_type,
                                                    "category_id": x.category.id,
                                                    "category_name": x.category.name,
                                                    "transaction_date": x.transaction_date,
                                                    "description": x.description,
                                                    "created_at": x.created_at,
                                                } for x in transactions_page]
                                            except Exception as e:
                                                logger.error("Transaction list formatting failed.", str(e))

                                            response["success"] = True
                                            response["data"]["transactions_info"] = paginated_transactions
                                            response["meta"]["pagination"] = {
                                                "page": transactions_page.number,
                                                "page_size": page_size,
                                                "total_pages": paginator.num_pages,
                                                "total_records": paginator.count,
                                                "has_next": transactions_page.has_next(),
                                                "has_previous": transactions_page.has_previous(),
                                            }
                                        else:
                                            response["success"] = False
                                            response["errors"].append("Unable to paginate transaction data.")
                                            response["error_code"] = 200418
                                else:
                                    response["success"] = False
                                    response["errors"].append("Transactions not found.")
                                    response["error_code"] = 200419
                            else:
                                response["success"] = False
                                response["errors"].append("User not authorized to access transaction records.")
                                response["error_code"] = 100416
                        else:
                            response["success"] = False
                            response["errors"].append("User profile not found.")
                            response["error_code"] = 100420
                else:
                    response["success"] = False
                    response["errors"].append("Invalid session.")
                    response["error_code"] = 100415
            else:
                response["success"] = False
                response["errors"].append("Invalid token.")
                response["error_code"] = 100412
        else:
            response["success"] = False
            response["errors"].append("User not found.")
            response["error_code"] = 100404
    else:
        response["success"] = False
        response["errors"].append("Invalid input, required fields not provided.")
        response["error_code"] = 100401

    return response


def get_transaction_record_detail(transaction_info):
    response = get_response_format()

    loggedin_user_obj = None
    loggedin_auth_token_obj = None
    loggedin_session_obj = None
    loggedin_profile_obj = None
    transaction_obj = None

    if transaction_info["loggedin_username"] and transaction_info["auth_token"] and \
       transaction_info["session_id"] and transaction_info["device_token"] and \
       transaction_info["transaction_id"]:

        try:
            loggedin_user_obj = User.objects.get(
                username=transaction_info["loggedin_username"],
                is_active=True
            )
        except Exception as e:
            logger.error("Logged in user not found.", str(e))

        if loggedin_user_obj:
            try:
                loggedin_auth_token_obj = UserAuthToken.objects.get(
                    user=loggedin_user_obj,
                    token=transaction_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Logged in user auth token not found.", str(e))

            if loggedin_auth_token_obj:
                try:
                    loggedin_session_obj = UserSession.objects.get(
                        user=loggedin_user_obj,
                        auth_token=loggedin_auth_token_obj,
                        session_id=transaction_info["session_id"],
                        device_token=transaction_info["device_token"],
                        logged_in=True
                    )
                except Exception as e:
                    logger.error("Logged in user session not found.", str(e))

                if loggedin_session_obj:
                    if timezone.now() > loggedin_session_obj.expiry_at:
                        response["success"] = False
                        response["errors"].append("Session expired.")
                        response["error_code"] = 100414
                    else:
                        try:
                            loggedin_profile_obj = UserProfile.objects.get(
                                user=loggedin_user_obj,
                                is_active=True
                            )
                        except Exception as e:
                            logger.error("Logged in user profile not found.", str(e))

                        if loggedin_profile_obj:
                            if loggedin_profile_obj.role.role_code in [ROLE_ADMIN, ROLE_ANALYST, ROLE_CLIENT]:
                                try:
                                    transaction_obj = Transaction.objects.select_related("category").get(
                                        transaction_id=transaction_info["transaction_id"],
                                        is_active=True,
                                        category__is_active=True
                                    )
                                except Exception as e:
                                    logger.error("Transaction not found.", str(e))

                                if transaction_obj:
                                    response["success"] = True
                                    response["data"]["transaction_info"] = {
                                        "transaction_id": str(transaction_obj.transaction_id),
                                        "title": transaction_obj.title,
                                        "amount": str(transaction_obj.amount),
                                        "transaction_type": transaction_obj.transaction_type,
                                        "category_id": transaction_obj.category.id,
                                        "category_name": transaction_obj.category.name,
                                        "transaction_date": transaction_obj.transaction_date,
                                        "description": transaction_obj.description,
                                        "is_active": transaction_obj.is_active,
                                        "created_at": transaction_obj.created_at,
                                        "updated_at": transaction_obj.updated_at,
                                    }
                                else:
                                    response["success"] = False
                                    response["errors"].append("Transaction not found.")
                                    response["error_code"] = 200415
                            else:
                                response["success"] = False
                                response["errors"].append("User not authorized to access transaction detail.")
                                response["error_code"] = 100416
                        else:
                            response["success"] = False
                            response["errors"].append("User profile not found.")
                            response["error_code"] = 100420
                else:
                    response["success"] = False
                    response["errors"].append("Invalid session.")
                    response["error_code"] = 100415
            else:
                response["success"] = False
                response["errors"].append("Invalid token.")
                response["error_code"] = 100412
        else:
            response["success"] = False
            response["errors"].append("User not found.")
            response["error_code"] = 100404
    else:
        response["success"] = False
        response["errors"].append("Invalid input, required fields not provided.")
        response["error_code"] = 100401

    return response


def delete_transaction_record(transaction_info):
    response = get_response_format()

    loggedin_user_obj = None
    loggedin_auth_token_obj = None
    loggedin_session_obj = None
    loggedin_profile_obj = None
    transaction_obj = None
    audit_log_obj = None

    if transaction_info["loggedin_username"] and transaction_info["auth_token"] and \
       transaction_info["session_id"] and transaction_info["device_token"] and \
       transaction_info["transaction_id"]:

        try:
            loggedin_user_obj = User.objects.get(
                username=transaction_info["loggedin_username"],
                is_active=True
            )
        except Exception as e:
            logger.error("Logged in user not found.", str(e))

        if loggedin_user_obj:
            try:
                loggedin_auth_token_obj = UserAuthToken.objects.get(
                    user=loggedin_user_obj,
                    token=transaction_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Logged in user auth token not found.", str(e))

            if loggedin_auth_token_obj:
                try:
                    loggedin_session_obj = UserSession.objects.get(
                        user=loggedin_user_obj,
                        auth_token=loggedin_auth_token_obj,
                        session_id=transaction_info["session_id"],
                        device_token=transaction_info["device_token"],
                        logged_in=True
                    )
                except Exception as e:
                    logger.error("Logged in user session not found.", str(e))

                if loggedin_session_obj:
                    if timezone.now() > loggedin_session_obj.expiry_at:
                        response["success"] = False
                        response["errors"].append("Session expired.")
                        response["error_code"] = 100414
                    else:
                        try:
                            loggedin_profile_obj = UserProfile.objects.get(
                                user=loggedin_user_obj,
                                is_active=True
                            )
                        except Exception as e:
                            logger.error("Logged in user profile not found.", str(e))

                        if loggedin_profile_obj:
                            if loggedin_profile_obj.role.role_code == ROLE_ADMIN:
                                try:
                                    transaction_obj = Transaction.objects.get(
                                        transaction_id=transaction_info["transaction_id"],
                                        is_active=True
                                    )
                                except Exception as e:
                                    logger.error("Transaction not found.", str(e))

                                if transaction_obj:
                                    try:
                                        transaction_obj.is_active = False
                                        transaction_obj.updated_by = loggedin_user_obj
                                        transaction_obj.save()
                                    except Exception as e:
                                        logger.error("Transaction delete failed.", str(e), transaction_info)

                                    if transaction_obj:
                                        try:
                                            audit_log_obj = TransactionAuditLog(
                                                transaction=transaction_obj,
                                                action=TRANSACTION_AUDIT_ACTION_DELETE,
                                                action_by=loggedin_user_obj,
                                                remarks="Transaction deleted."
                                            )
                                            audit_log_obj.save()
                                        except Exception as e:
                                            logger.error("Transaction audit log save failed.", str(e), transaction_info)

                                        response["success"] = True
                                        response["data"]["transaction_info"] = {
                                            "transaction_id": str(transaction_obj.transaction_id),
                                            "deleted": True,
                                        }
                                    else:
                                        response["success"] = False
                                        response["errors"].append("Transaction not deleted.")
                                        response["error_code"] = 200420
                                else:
                                    response["success"] = False
                                    response["errors"].append("Transaction not found.")
                                    response["error_code"] = 200415
                            else:
                                response["success"] = False
                                response["errors"].append("User not authorized to delete transaction.")
                                response["error_code"] = 100416
                        else:
                            response["success"] = False
                            response["errors"].append("User profile not found.")
                            response["error_code"] = 100420
                else:
                    response["success"] = False
                    response["errors"].append("Invalid session.")
                    response["error_code"] = 100415
            else:
                response["success"] = False
                response["errors"].append("Invalid token.")
                response["error_code"] = 100412
        else:
            response["success"] = False
            response["errors"].append("User not found.")
            response["error_code"] = 100404
    else:
        response["success"] = False
        response["errors"].append("Invalid input, required fields not provided.")
        response["error_code"] = 100401

    return response