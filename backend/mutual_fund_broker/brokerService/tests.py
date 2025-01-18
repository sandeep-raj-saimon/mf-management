from rest_framework.test import APITestCase
from rest_framework import status
from .models import *
from decimal import Decimal
class FetchFundFamiliesTestCase(APITestCase):
    def test_fetch_fund_families(self):
        url = "http://127.0.0.1:8000/api/broker/fetch-fund-families/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("created_families", response.data)
        # Check if fund families are created in the database
        self.assertGreater(FundFamily.objects.count(), 0)

class UpdateOrCreateNAVTestCase(APITestCase):
    def setUp(self):
        self.url = "http://127.0.0.1:8000/api/broker/update-or-create-nav/"
        self.fund_family = FundFamily.objects.create(name="Test Fund Family")
        self.mutual_fund = MutualFundScheme.objects.create(
            fund_family=self.fund_family,
            scheme_name="Test Mutual Fund",
            nav=100.0
        )

    def test_update_nav(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        # Check if NAV is updated
        updated_fund = MutualFundScheme.objects.get(id=self.mutual_fund.id)
        self.assertEqual(updated_fund.nav, 100.0)  # NAV should have been updated

class FetchPortfolioTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="testuser@example.com", password="securepassword123")
        self.portfolio = Portfolio.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)

    def test_fetch_portfolio(self):
        url = "http://127.0.0.1:8000/api/broker/portfolio-details/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)

class BuyMutualFundTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="testuser@example.com", password="securepassword123", balance=Decimal(5000))
        self.fund_family = FundFamily.objects.create(name="Test Fund Family")
        self.portfolio = Portfolio.objects.create(user=self.user)
        self.mutual_fund = MutualFundScheme.objects.create(
            fund_family=self.fund_family,
            scheme_name="Test Mutual Fund",
            nav=100.0
        )
        self.client.force_authenticate(user=self.user)

    def test_buy_mutual_fund(self):
        url = "http://127.0.0.1:8000/api/broker/buy-mutual-fund/"
        data = {
            "mutual_fund_id": self.mutual_fund.id,
            "units": 10
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("remaining_balance", response.data)
        # Check if investment is created
        self.assertTrue(Investment.objects.filter(portfolio__user=self.user, mutual_fund_scheme=self.mutual_fund).exists())