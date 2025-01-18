from celery import shared_task
from brokerService.models import FundFamily, MutualFundScheme
import requests

@shared_task
def update_or_create_nav():
    url = "https://latest-mutual-fund-nav.p.rapidapi.com/latest"
    headers = {
        "X-RapidAPI-Key": 'cbc2bb2a45msh6a422ea24d5584fp1147c4jsn1288ccf8c49f',
        "X-RapidAPI-Host": "latest-mutual-fund-nav.p.rapidapi.com",
    }
    updated_schemes = []
    created_schemes = []

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            schemes_data = response.json()
            for scheme_data in schemes_data:
                fund_family_name = scheme_data.get("Mutual_Fund_Family")
                scheme_name = scheme_data.get("Scheme_Name")
                nav = scheme_data.get("Net_Asset_Value")
                scheme_type = scheme_data.get("Scheme_Type", "Open Ended")

                fund_family, _ = FundFamily.objects.get_or_create(name=fund_family_name)
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
    except Exception as e:
        print(f"Error updating or creating schemes: {e}")

@shared_task
def fetch_fund_families():
    url = "https://latest-mutual-fund-nav.p.rapidapi.com/latest"
    headers = {
        "X-RapidAPI-Key": 'cbc2bb2a45msh6a422ea24d5584fp1147c4jsn1288ccf8c49f',
        "X-RapidAPI-Host": "latest-mutual-fund-nav.p.rapidapi.com",
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            fund_families = {scheme["Mutual_Fund_Family"] for scheme in data}
            for family_name in fund_families:
                FundFamily.objects.get_or_create(name=family_name)
    except Exception as e:
        print(f"Error fetching fund families: {e}")
