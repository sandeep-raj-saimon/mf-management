from django.db import models
from userService.models import *
# Create your models here.
class FundFamily(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class MutualFundScheme(models.Model):
    fund_family = models.ForeignKey(FundFamily, on_delete=models.CASCADE, related_name="schemes")
    scheme_name = models.CharField(max_length=255)
    scheme_type = models.CharField(max_length=50)  # e.g., "Open Ended", "Closed Ended"
    nav = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Net Asset Value
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.scheme_name} ({self.fund_family.name})"

class Portfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="portfolio")

    def __str__(self):
        return f"{self.user.email}'s Portfolio"

class Investment(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="investments")
    mutual_fund_scheme = models.ForeignKey(MutualFundScheme, on_delete=models.CASCADE)
    units = models.DecimalField(max_digits=10, decimal_places=2)  # Number of units purchased
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)  # NAV at the time of purchase
    purchase_date = models.DateTimeField(auto_now_add=True)
    current_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.portfolio.user.email} - {self.mutual_fund_scheme.scheme_name}"

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]

    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    units = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)  # NAV at the time of transaction
    transaction_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.investment.mutual_fund_scheme.scheme_name}"

class NAVUpdateLog(models.Model):
    mutual_fund_scheme = models.ForeignKey(MutualFundScheme, on_delete=models.CASCADE, related_name="nav_updates")
    nav = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.mutual_fund_scheme.scheme_name} - NAV: {self.nav}"
