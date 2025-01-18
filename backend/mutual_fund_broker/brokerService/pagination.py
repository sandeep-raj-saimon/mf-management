from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class TransactionPagination(PageNumberPagination):
    page_size = 10  # Number of transactions per page
    page_size_query_param = 'page_size'  # Allow clients to customize page size
    max_page_size = 100  # Set a maximum page size

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,  # Total number of transactions
            'next': self.get_next_link(),  # URL for the next page
            'previous': self.get_previous_link(),  # URL for the previous page
            'results': data,  # Paginated data
        })