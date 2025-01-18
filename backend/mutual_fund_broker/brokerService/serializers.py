from rest_framework import serializers
from .models import MutualFundScheme, Investment, Transaction

class FundFamilySerializer(serializers.Serializer):
    fund_family_name = serializers.CharField(max_length=255)

class MutualFundSchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MutualFundScheme
        fields = ['scheme_name', 'scheme_type', 'nav', 'last_updated']

class InvestmentSerializer(serializers.ModelSerializer):
    mutual_fund_scheme_name = serializers.CharField(source="mutual_fund_scheme.scheme_name", read_only=True)
    profit_or_loss = serializers.SerializerMethodField()

    class Meta:
        model = Investment
        fields = [
            "mutual_fund_scheme_name",
            "units",
            "purchase_price",
            "current_value",
            "profit_or_loss",
            "purchase_date",
        ]

    def get_profit_or_loss(self, obj):
        """
        Calculate the profit or loss for the investment.
        """
        if obj.current_value and obj.units:
            return round(obj.current_value - (obj.units * obj.purchase_price), 2)
        return 0.00
    
class TransactionSerializer(serializers.ModelSerializer):
    transaction_type_display = serializers.CharField(source="get_transaction_type_display", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "transaction_type",
            "transaction_type_display",
            "units",
            "price_per_unit",
            "transaction_date",
        ]