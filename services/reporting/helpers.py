import logging
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, Count
from django.db.models.functions import ExtractMonth
from django.utils import timezone

from utilities.utils import get_response_format
from utilities.constants import ROLE_ADMIN, ROLE_ANALYST, ROLE_CLIENT, TRANSACTION_TYPE_INCOME, \
    TRANSACTION_TYPE_EXPENSE

from services.users.models import UserAuthToken, UserSession, UserProfile
from services.transactions.models import Transaction, TransactionAuditLog

logger = logging.getLogger(__name__)


def get_dashboard_summary(summary_info):
    response = get_response_format()

    loggedin_user_obj = None
    loggedin_auth_token_obj = None
    loggedin_session_obj = None
    loggedin_profile_obj = None
    transactions_queryset = None

    total_income = Decimal("0.00")
    total_expense = Decimal("0.00")
    net_balance = Decimal("0.00")
    total_transactions = 0
    parsed_start_date = None
    parsed_end_date = None

    if summary_info["loggedin_username"] and summary_info["auth_token"] and \
       summary_info["session_id"] and summary_info["device_token"]:

        try:
            loggedin_user_obj = User.objects.get(
                username=summary_info["loggedin_username"],
                is_active=True
            )
        except Exception as e:
            logger.error("Logged in user not found.", str(e))

        if loggedin_user_obj:
            try:
                loggedin_auth_token_obj = UserAuthToken.objects.get(
                    user=loggedin_user_obj,
                    token=summary_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Logged in user auth token not found.", str(e))

            if loggedin_auth_token_obj:
                try:
                    loggedin_session_obj = UserSession.objects.get(
                        user=loggedin_user_obj,
                        auth_token=loggedin_auth_token_obj,
                        session_id=summary_info["session_id"],
                        device_token=summary_info["device_token"],
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
                                    transactions_queryset = Transaction.objects.filter(
                                        is_active=True,
                                        category__is_active=True
                                    )
                                except Exception as e:
                                    logger.error("Dashboard summary transaction fetch failed.", str(e))

                                if transactions_queryset is not None:
                                    if summary_info["start_date"]:
                                        try:
                                            parsed_start_date = datetime.strptime(
                                                summary_info["start_date"], "%Y-%m-%d"
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
                                            response["error_code"] = 300401

                                    if summary_info["end_date"] and len(response["errors"]) == 0:
                                        try:
                                            parsed_end_date = datetime.strptime(
                                                summary_info["end_date"], "%Y-%m-%d"
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
                                            response["error_code"] = 300402

                                    if len(response["errors"]) == 0:
                                        try:
                                            total_income_data = transactions_queryset.filter(
                                                transaction_type=TRANSACTION_TYPE_INCOME
                                            ).aggregate(total_amount=Sum("amount"))

                                            total_expense_data = transactions_queryset.filter(
                                                transaction_type=TRANSACTION_TYPE_EXPENSE
                                            ).aggregate(total_amount=Sum("amount"))

                                            total_transactions = transactions_queryset.count()
                                        except Exception as e:
                                            logger.error("Dashboard summary aggregation failed.", str(e))

                                        if total_income_data and total_income_data["total_amount"] is not None:
                                            total_income = total_income_data["total_amount"]

                                        if total_expense_data and total_expense_data["total_amount"] is not None:
                                            total_expense = total_expense_data["total_amount"]

                                        net_balance = total_income - total_expense

                                        response["success"] = True
                                        response["data"]["dashboard_summary"] = {
                                            "total_income": str(total_income),
                                            "total_expense": str(total_expense),
                                            "net_balance": str(net_balance),
                                            "total_transactions": total_transactions,
                                            "start_date": parsed_start_date,
                                            "end_date": parsed_end_date,
                                        }
                                else:
                                    response["success"] = False
                                    response["errors"].append("Transaction data not found.")
                                    response["error_code"] = 300403
                            else:
                                response["success"] = False
                                response["errors"].append("User not authorized to access dashboard summary.")
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


def get_category_wise_summary(summary_info):
    response = get_response_format()

    loggedin_user_obj = None
    loggedin_auth_token_obj = None
    loggedin_session_obj = None
    loggedin_profile_obj = None
    transactions_queryset = None
    category_summary = []

    parsed_start_date = None
    parsed_end_date = None

    if summary_info["loggedin_username"] and summary_info["auth_token"] and \
       summary_info["session_id"] and summary_info["device_token"]:

        try:
            loggedin_user_obj = User.objects.get(
                username=summary_info["loggedin_username"],
                is_active=True
            )
        except Exception as e:
            logger.error("Logged in user not found.", str(e))

        if loggedin_user_obj:
            try:
                loggedin_auth_token_obj = UserAuthToken.objects.get(
                    user=loggedin_user_obj,
                    token=summary_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Logged in user auth token not found.", str(e))

            if loggedin_auth_token_obj:
                try:
                    loggedin_session_obj = UserSession.objects.get(
                        user=loggedin_user_obj,
                        auth_token=loggedin_auth_token_obj,
                        session_id=summary_info["session_id"],
                        device_token=summary_info["device_token"],
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
                                    transactions_queryset = Transaction.objects.filter(
                                        is_active=True,
                                        category__is_active=True
                                    )
                                except Exception as e:
                                    logger.error("Category summary transaction fetch failed.", str(e))

                                if transactions_queryset is not None:
                                    if summary_info["transaction_type"]:
                                        if summary_info["transaction_type"] in [TRANSACTION_TYPE_INCOME, TRANSACTION_TYPE_EXPENSE]:
                                            transactions_queryset = transactions_queryset.filter(
                                                transaction_type=summary_info["transaction_type"]
                                            )
                                        else:
                                            response["success"] = False
                                            response["errors"].append("Invalid transaction type.")
                                            response["error_code"] = 300404

                                    if summary_info["start_date"] and len(response["errors"]) == 0:
                                        try:
                                            parsed_start_date = datetime.strptime(
                                                summary_info["start_date"], "%Y-%m-%d"
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
                                            response["error_code"] = 300401

                                    if summary_info["end_date"] and len(response["errors"]) == 0:
                                        try:
                                            parsed_end_date = datetime.strptime(
                                                summary_info["end_date"], "%Y-%m-%d"
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
                                            response["error_code"] = 300402

                                    if len(response["errors"]) == 0:
                                        try:
                                            category_summary_queryset = transactions_queryset.values(
                                                "category__id",
                                                "category__name",
                                                "transaction_type"
                                            ).annotate(
                                                total_amount=Sum("amount"),
                                                total_transactions=Count("id")
                                            ).order_by("category__name")
                                        except Exception as e:
                                            category_summary_queryset = []
                                            logger.error("Category summary aggregation failed.", str(e))

                                        try:
                                            category_summary = [{
                                                "category_id": x["category__id"],
                                                "category_name": x["category__name"],
                                                "transaction_type": x["transaction_type"],
                                                "total_amount": str(x["total_amount"]) if x["total_amount"] is not None else "0.00",
                                                "total_transactions": x["total_transactions"],
                                            } for x in category_summary_queryset]
                                        except Exception as e:
                                            logger.error("Category summary formatting failed.", str(e))

                                        response["success"] = True
                                        response["data"]["category_summary"] = category_summary
                                else:
                                    response["success"] = False
                                    response["errors"].append("Transaction data not found.")
                                    response["error_code"] = 300403
                            else:
                                response["success"] = False
                                response["errors"].append("User not authorized to access category summary.")
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


def get_monthly_transaction_trend(trend_info):
    response = get_response_format()

    loggedin_user_obj = None
    loggedin_auth_token_obj = None
    loggedin_session_obj = None
    loggedin_profile_obj = None
    transactions_queryset = None
    monthly_data = []
    monthly_map = {}

    if trend_info["loggedin_username"] and trend_info["auth_token"] and \
       trend_info["session_id"] and trend_info["device_token"] and \
       trend_info["year"]:

        try:
            loggedin_user_obj = User.objects.get(
                username=trend_info["loggedin_username"],
                is_active=True
            )
        except Exception as e:
            logger.error("Logged in user not found.", str(e))

        if loggedin_user_obj:
            try:
                loggedin_auth_token_obj = UserAuthToken.objects.get(
                    user=loggedin_user_obj,
                    token=trend_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Logged in user auth token not found.", str(e))

            if loggedin_auth_token_obj:
                try:
                    loggedin_session_obj = UserSession.objects.get(
                        user=loggedin_user_obj,
                        auth_token=loggedin_auth_token_obj,
                        session_id=trend_info["session_id"],
                        device_token=trend_info["device_token"],
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
                                    year_value = int(trend_info["year"])
                                except Exception as e:
                                    year_value = None
                                    logger.error("Invalid year.", str(e))

                                if year_value:
                                    try:
                                        transactions_queryset = Transaction.objects.filter(
                                            is_active=True,
                                            category__is_active=True,
                                            transaction_date__year=year_value
                                        )
                                    except Exception as e:
                                        logger.error("Monthly trend transaction fetch failed.", str(e))

                                    if transactions_queryset is not None:
                                        if trend_info["transaction_type"]:
                                            if trend_info["transaction_type"] in [TRANSACTION_TYPE_INCOME, TRANSACTION_TYPE_EXPENSE]:
                                                transactions_queryset = transactions_queryset.filter(
                                                    transaction_type=trend_info["transaction_type"]
                                                )
                                            else:
                                                response["success"] = False
                                                response["errors"].append("Invalid transaction type.")
                                                response["error_code"] = 300404

                                        if len(response["errors"]) == 0:
                                            try:
                                                monthly_queryset = transactions_queryset.annotate(
                                                    month=ExtractMonth("transaction_date")
                                                ).values(
                                                    "month",
                                                    "transaction_type"
                                                ).annotate(
                                                    total_amount=Sum("amount"),
                                                    total_transactions=Count("id")
                                                ).order_by("month")
                                            except Exception as e:
                                                monthly_queryset = []
                                                logger.error("Monthly trend aggregation failed.", str(e))

                                            for month_number in range(1, 13):
                                                monthly_map[month_number] = {
                                                    "month": month_number,
                                                    "income_total": Decimal("0.00"),
                                                    "expense_total": Decimal("0.00"),
                                                    "income_transactions": 0,
                                                    "expense_transactions": 0,
                                                }

                                            for item in monthly_queryset:
                                                if item["transaction_type"] == TRANSACTION_TYPE_INCOME:
                                                    monthly_map[item["month"]]["income_total"] = item["total_amount"] or Decimal("0.00")
                                                    monthly_map[item["month"]]["income_transactions"] = item["total_transactions"]
                                                elif item["transaction_type"] == TRANSACTION_TYPE_EXPENSE:
                                                    monthly_map[item["month"]]["expense_total"] = item["total_amount"] or Decimal("0.00")
                                                    monthly_map[item["month"]]["expense_transactions"] = item["total_transactions"]

                                            for month_number in range(1, 13):
                                                income_total = monthly_map[month_number]["income_total"]
                                                expense_total = monthly_map[month_number]["expense_total"]

                                                monthly_data.append({
                                                    "month": month_number,
                                                    "income_total": str(income_total),
                                                    "expense_total": str(expense_total),
                                                    "net_total": str(income_total - expense_total),
                                                    "income_transactions": monthly_map[month_number]["income_transactions"],
                                                    "expense_transactions": monthly_map[month_number]["expense_transactions"],
                                                })

                                            response["success"] = True
                                            response["data"]["monthly_trend"] = monthly_data
                                    else:
                                        response["success"] = False
                                        response["errors"].append("Transaction data not found.")
                                        response["error_code"] = 300403
                                else:
                                    response["success"] = False
                                    response["errors"].append("Invalid year.")
                                    response["error_code"] = 300405
                            else:
                                response["success"] = False
                                response["errors"].append("User not authorized to access monthly trend.")
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


def get_recent_transaction_activity(activity_info):
    response = get_response_format()

    loggedin_user_obj = None
    loggedin_auth_token_obj = None
    loggedin_session_obj = None
    loggedin_profile_obj = None
    recent_transactions_queryset = None
    recent_transactions = []

    limit = 5

    if activity_info["loggedin_username"] and activity_info["auth_token"] and \
       activity_info["session_id"] and activity_info["device_token"]:

        if activity_info["limit"]:
            try:
                limit = int(activity_info["limit"])
            except Exception as e:
                logger.error("Invalid limit value.", str(e))

        try:
            loggedin_user_obj = User.objects.get(
                username=activity_info["loggedin_username"],
                is_active=True
            )
        except Exception as e:
            logger.error("Logged in user not found.", str(e))

        if loggedin_user_obj:
            try:
                loggedin_auth_token_obj = UserAuthToken.objects.get(
                    user=loggedin_user_obj,
                    token=activity_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Logged in user auth token not found.", str(e))

            if loggedin_auth_token_obj:
                try:
                    loggedin_session_obj = UserSession.objects.get(
                        user=loggedin_user_obj,
                        auth_token=loggedin_auth_token_obj,
                        session_id=activity_info["session_id"],
                        device_token=activity_info["device_token"],
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
                                    recent_transactions_queryset = Transaction.objects.select_related(
                                        "category"
                                    ).filter(
                                        is_active=True,
                                        category__is_active=True
                                    ).order_by("-created_at")[:limit]
                                except Exception as e:
                                    logger.error("Recent transaction activity fetch failed.", str(e))

                                if recent_transactions_queryset is not None:
                                    try:
                                        recent_transactions = [{
                                            "transaction_id": str(x.transaction_id),
                                            "title": x.title,
                                            "amount": str(x.amount),
                                            "transaction_type": x.transaction_type,
                                            "category_id": x.category.id,
                                            "category_name": x.category.name,
                                            "transaction_date": x.transaction_date,
                                            "description": x.description,
                                            "created_at": x.created_at,
                                        } for x in recent_transactions_queryset]
                                    except Exception as e:
                                        logger.error("Recent transaction activity formatting failed.", str(e))

                                    response["success"] = True
                                    response["data"]["recent_transactions"] = recent_transactions
                                else:
                                    response["success"] = False
                                    response["errors"].append("Recent transaction activity not found.")
                                    response["error_code"] = 300406
                            else:
                                response["success"] = False
                                response["errors"].append("User not authorized to access recent transaction activity.")
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


def get_transaction_audit_logs(audit_info):
    response = get_response_format()

    loggedin_user_obj = None
    loggedin_auth_token_obj = None
    loggedin_session_obj = None
    loggedin_profile_obj = None
    audit_queryset = None
    paginated_audit_logs = []

    page = 1
    page_size = 10

    if audit_info["loggedin_username"] and audit_info["auth_token"] and \
       audit_info["session_id"] and audit_info["device_token"]:

        if audit_info["page"]:
            page = audit_info["page"]

        if audit_info["page_size"]:
            page_size = audit_info["page_size"]

        try:
            loggedin_user_obj = User.objects.get(
                username=audit_info["loggedin_username"],
                is_active=True
            )
        except Exception as e:
            logger.error("Logged in user not found.", str(e))

        if loggedin_user_obj:
            try:
                loggedin_auth_token_obj = UserAuthToken.objects.get(
                    user=loggedin_user_obj,
                    token=audit_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Logged in user auth token not found.", str(e))

            if loggedin_auth_token_obj:
                try:
                    loggedin_session_obj = UserSession.objects.get(
                        user=loggedin_user_obj,
                        auth_token=loggedin_auth_token_obj,
                        session_id=audit_info["session_id"],
                        device_token=audit_info["device_token"],
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
                            if loggedin_profile_obj.role.role_code in [ROLE_ADMIN, ROLE_ANALYST]:
                                try:
                                    audit_queryset = TransactionAuditLog.objects.select_related(
                                        "transaction",
                                        "action_by"
                                    ).order_by("-id")
                                except Exception as e:
                                    logger.error("Transaction audit log fetch failed.", str(e))

                                if audit_queryset is not None:
                                    if audit_info["transaction_id"]:
                                        audit_queryset = audit_queryset.filter(
                                            transaction__transaction_id=audit_info["transaction_id"]
                                        )

                                    try:
                                        paginator = Paginator(audit_queryset, page_size)
                                        audit_page = paginator.page(page)
                                    except PageNotAnInteger:
                                        audit_page = paginator.page(1)
                                    except EmptyPage:
                                        audit_page = paginator.page(paginator.num_pages)
                                    except Exception as e:
                                        audit_page = None
                                        logger.error("Transaction audit log pagination failed.", str(e))

                                    if audit_page:
                                        try:
                                            paginated_audit_logs = [{
                                                "audit_log_id": x.id,
                                                "transaction_id": str(x.transaction.transaction_id),
                                                "action": x.action,
                                                "action_by": x.action_by.username if x.action_by else None,
                                                "remarks": x.remarks,
                                                "created_at": x.created_at,
                                            } for x in audit_page]
                                        except Exception as e:
                                            logger.error("Transaction audit log formatting failed.", str(e))

                                        response["success"] = True
                                        response["data"]["audit_logs"] = paginated_audit_logs
                                        response["meta"]["pagination"] = {
                                            "page": audit_page.number,
                                            "page_size": page_size,
                                            "total_pages": paginator.num_pages,
                                            "total_records": paginator.count,
                                            "has_next": audit_page.has_next(),
                                            "has_previous": audit_page.has_previous(),
                                        }
                                    else:
                                        response["success"] = False
                                        response["errors"].append("Unable to paginate audit log data.")
                                        response["error_code"] = 300407
                                else:
                                    response["success"] = False
                                    response["errors"].append("Transaction audit logs not found.")
                                    response["error_code"] = 300408
                            else:
                                response["success"] = False
                                response["errors"].append("User not authorized to access transaction audit logs.")
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