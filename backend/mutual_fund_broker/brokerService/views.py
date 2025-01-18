from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from decouple import config
from decimal import Decimal
from .models import *
from .pagination import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction as db_transaction
import logging

logger = logging.getLogger(__name__)


class UpdateOrCreateNAVAPIView(APIView):
    """
    API endpoint to update NAV for existing schemes or create new ones if they don't exist.
    """
    permission_classes = [AllowAny]
    def post(self, request):
        url = "https://latest-mutual-fund-nav.p.rapidapi.com/latest"  # Replace with the actual API endpoint
        headers = {
            "X-RapidAPI-Key": 'cbc2bb2a45msh6a422ea24d5584fp1147c4jsn1288ccf8c49f',
            "X-RapidAPI-Host": "latest-mutual-fund-nav.p.rapidapi.com",
        }
        updated_schemes = []
        created_schemes = []

        try:
            # Fetch all mutual fund schemes from the third-party API
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                schemes_data = response.json()  # Assuming this returns a list of schemes
                for scheme_data in schemes_data:
                    fund_family_name = scheme_data.get("Mutual_Fund_Family")
                    scheme_name = scheme_data.get("Scheme_Name")
                    nav = scheme_data.get("Net_Asset_Value")
                    scheme_type = scheme_data.get("Scheme_Type", "Open Ended")
                    # Get or create the fund family
                    fund_family, _ = FundFamily.objects.get_or_create(name=fund_family_name)

                    # Update or create the mutual fund scheme
                    scheme, created = MutualFundScheme.objects.update_or_create(
                        fund_family=fund_family,
                        scheme_name=scheme_name,
                        defaults={
                            "nav": nav,
                            "scheme_type": scheme_type,
                        }
                    )

                    if created:
                        created_schemes.append(scheme_name)
                    else:
                        updated_schemes.append(scheme_name)
                
                return Response({
                    "message": "NAV updated successfully",
                    "updated_schemes": updated_schemes,
                    "created_schemes": created_schemes,
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": "Failed to fetch data from third-party API",
                    "status_code": response.status_code
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(f"Error updating or creating schemes: {e}")
            return Response({"error": "An error occurred while processing NAV data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FetchFundFamiliesAPIView(APIView):
    """
    API endpoint to fetch and save all mutual fund families to the database.
    """
    permission_classes = [AllowAny]
    def post(self, request):
        url = "https://latest-mutual-fund-nav.p.rapidapi.com/latest"  # Replace with the actual API endpoint
        headers = {
            "X-RapidAPI-Key": 'cbc2bb2a45msh6a422ea24d5584fp1147c4jsn1288ccf8c49f',
            "X-RapidAPI-Host": "latest-mutual-fund-nav.p.rapidapi.com",
        }

        try:
            # Make a request to the third-party API
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()  # Assuming this returns the list of schemes
                fund_families = {scheme["Mutual_Fund_Family"] for scheme in data}

                # Save each fund family to the database
                created_families = []
                for family_name in fund_families:
                    _, created = FundFamily.objects.get_or_create(name=family_name)
                    if created:
                        created_families.append(family_name)

                return Response({
                    "message": "Fund families fetched and saved successfully",
                    "created_families": created_families,
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": "Failed to fetch data from the API",
                    "status_code": response.status_code,
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            print(f"Error fetching fund families: {e}")
            return Response({
                "error": "An error occurred while processing the request",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FetchOpenEndedSchemesAPIView(APIView):
    """
    Authenticated API to fetch open-ended schemes for a given fund family from the database.
    """
    permission_classes = [IsAuthenticated]  # Require authentication

    def get(self, request):
        # Get the 'fund_family_name' from query parameters
        fund_family_name = request.query_params.get('fund_family_name')

        if not fund_family_name:
            return Response(
                {"error": "Query parameter 'fund_family_name' is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if the fund family exists
        try:
            fund_family = FundFamily.objects.get(name=fund_family_name)
        except FundFamily.DoesNotExist:
            return Response(
                {"error": f"Fund family '{fund_family_name}' does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Fetch open-ended schemes for the fund family from the database
        open_ended_schemes = MutualFundScheme.objects.filter(
            fund_family=fund_family, scheme_type="Open Ended Schemes"
        )

        # If no open-ended schemes are found
        if not open_ended_schemes.exists():
            return Response(
                {"message": f"No open-ended schemes found for fund family '{fund_family_name}'."},
                status=status.HTTP_200_OK
            )

        # Serialize and return the schemes
        serialized_schemes = MutualFundSchemeSerializer(open_ended_schemes, many=True)
        return Response(
            {"fund_family": fund_family.name, "schemes": serialized_schemes.data},
            status=status.HTTP_200_OK
        )

class BuyMutualFundAPIView(APIView):
    """
    API to buy units of a mutual fund. Updates the investment and creates a transaction.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        portfolio = user.portfolio  # Assuming a `OneToOneField` exists between CustomUser and Portfolio
        mutual_fund_id = request.data.get('mutual_fund_id')
        units_to_buy = request.data.get('units')

        # Validate inputs
        if not mutual_fund_id or not units_to_buy:
            return Response({"error": "mutual_fund_id and units are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            mutual_fund_id = int(mutual_fund_id)
            mutual_fund = MutualFundScheme.objects.get(id=mutual_fund_id)
        except (ValueError, MutualFundScheme.DoesNotExist):
            return Response({"error": "Invalid mutual fund ID."}, status=status.HTTP_404_NOT_FOUND)

        try:
            units_to_buy = Decimal(units_to_buy)
            if units_to_buy <= 0:
                raise ValueError
        except ValueError:
            return Response({"error": "Units must be a positive number."}, status=status.HTTP_400_BAD_REQUEST)

        total_price = units_to_buy * Decimal(mutual_fund.nav)

        # Check user balance
        if user.balance < total_price:
            return Response(
                {
                    "error": "Insufficient balance.",
                    "required_balance": float(total_price),
                    "current_balance": float(user.balance),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Process the transaction
        try:
            with db_transaction.atomic():
                # Deduct the amount from the user's balance
                user.balance -= total_price
                user.save()
                # Find or create an investment record
                investment, created = Investment.objects.get_or_create(
                    portfolio=portfolio,
                    mutual_fund_scheme=mutual_fund,
                    defaults={
                        "units": 0,
                        "purchase_price": 0,
                        "current_value": 0,
                    },
                )

                # Update the investment's units and purchase price
                total_units = investment.units + units_to_buy
                investment.purchase_price = (
                    (investment.units * investment.purchase_price + total_price) / total_units
                )
                investment.units = total_units
                investment.current_value = total_units * Decimal(mutual_fund.nav)
                investment.save()

                # Record the transaction
                Transaction.objects.create(
                    investment=investment,
                    transaction_type='BUY',
                    units=units_to_buy,
                    price_per_unit=mutual_fund.nav,
                )

            return Response(
                {
                    "message": f"Successfully bought {units_to_buy} units of {mutual_fund.scheme_name}.",
                    "remaining_balance": float(user.balance),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error during mutual fund sale: {str(e)}")
            return Response({"error": "An error occurred while processing your transaction."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SellMutualFundAPIView(APIView):
    """
    API to sell units of a mutual fund. Updates the investment and creates a transaction.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        portfolio = user.portfolio  # Assuming a `OneToOneField` exists between CustomUser and Portfolio
        mutual_fund_id = request.data.get('mutual_fund_id')
        units_to_sell = request.data.get('units')

        # Validate inputs
        if not mutual_fund_id or not units_to_sell:
            return Response({"error": "mutual_fund_id and units are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            mutual_fund_id = int(mutual_fund_id)
            mutual_fund = MutualFundScheme.objects.get(id=mutual_fund_id)
        except (ValueError, MutualFundScheme.DoesNotExist):
            return Response({"error": "Invalid mutual fund ID."}, status=status.HTTP_404_NOT_FOUND)

        try:
            units_to_sell = Decimal(units_to_sell)
            if units_to_sell <= 0:
                raise ValueError
        except ValueError:
            return Response({"error": "Units must be a positive number."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user has an existing investment in the mutual fund
        try:
            investment = Investment.objects.get(portfolio=portfolio, mutual_fund_scheme=mutual_fund)
        except Investment.DoesNotExist:
            return Response({"error": "No investment found for the specified mutual fund."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user owns enough units to sell
        if investment.units < units_to_sell:
            return Response(
                {"error": "Insufficient units.", "owned_units": float(investment.units), "requested_units": float(units_to_sell)},
                status=status.HTTP_400_BAD_REQUEST
            )

        sale_price = units_to_sell * Decimal(mutual_fund.nav)

        # Process the transaction
        try:
            with db_transaction.atomic():
                # Deduct the units from the investment
                investment.units -= units_to_sell
                investment.current_value = investment.units * Decimal(mutual_fund.nav)

                # Record the transaction
                Transaction.objects.create(
                    investment=investment,
                    transaction_type='SELL',
                    units=units_to_sell,
                    price_per_unit=mutual_fund.nav,
                )

                if investment.units == 0:
                    investment.current_value = 0  # Reset current value to 0
                investment.save()

                # Add the sale amount to the user's balance
                user.balance += sale_price
                user.save()

            return Response(
                {
                    "message": f"Successfully sold {units_to_sell} units of {mutual_fund.scheme_name}.",
                    "sale_amount": float(sale_price),
                    "remaining_balance": float(user.balance),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error during mutual fund sale: {str(e)}")
            return Response({"error": "An error occurred while processing your transaction."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PortfolioDetailsAPIView(APIView):
    """
    API to fetch user portfolio details.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        portfolio = user.portfolio  # Assuming a OneToOneField exists between CustomUser and Portfolio

        # Fetch all investments in the user's portfolio
        investments = Investment.objects.filter(portfolio=portfolio)

        # If no investments are found
        if not investments.exists():
            return Response(
                {"error": "No investments found in your portfolio."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Serialize the investments
        serialized_investments = InvestmentSerializer(investments, many=True)

        # Calculate overall profit or loss
        overall_profit_or_loss = sum(
            (investment.current_value or 0) - (investment.units * investment.purchase_price or 0)
            for investment in investments
        )

        # Format the response
        return Response(
            {
                "portfolio_owner": user.email,
                "overall_profit_or_loss": round(overall_profit_or_loss, 2),
                "investments": serialized_investments.data,
            },
            status=status.HTTP_200_OK,
        )

class MutualFundTransactionsAPIView(APIView):
    """
    API to fetch all transactions for a specific mutual fund investment.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, mutual_fund_id):
        user = request.user
        portfolio = user.portfolio  # Assuming a `OneToOneField` exists between CustomUser and Portfolio

        try:
            mutual_fund = MutualFundScheme.objects.get(id=mutual_fund_id)
        except MutualFundScheme.DoesNotExist:
            return Response({"error": "Invalid mutual fund ID."}, status=status.HTTP_404_NOT_FOUND)

        try:
            investment = Investment.objects.get(portfolio=portfolio, mutual_fund_scheme=mutual_fund)
        except Investment.DoesNotExist:
            return Response({"error": "No investment found for the specified mutual fund."}, status=status.HTTP_404_NOT_FOUND)

        transactions = Transaction.objects.filter(investment=investment).order_by('-transaction_date')

        # Apply pagination
        paginator = TransactionPagination()
        paginated_transactions = paginator.paginate_queryset(transactions, request)
        serialized_transactions = TransactionSerializer(paginated_transactions, many=True)

        return paginator.get_paginated_response(serialized_transactions.data)