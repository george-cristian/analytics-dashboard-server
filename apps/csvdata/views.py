import asyncio
import traceback
from io import StringIO
from typing import Any, NoReturn

import pandas as pd
from asgiref.sync import async_to_sync, sync_to_async
from django.http import JsonResponse
from rest_framework import status, viewsets
from rest_framework.mixins import (ListModelMixin, RetrieveModelMixin,
                                   UpdateModelMixin)
from rest_framework.permissions import IsAuthenticated

from .models import CSVData
from .serializers import CSVDataSerializer


class CsvDataViewSet(ListModelMixin,
                  RetrieveModelMixin,
                  UpdateModelMixin,
                  viewsets.GenericViewSet):

    # allow only authenticated users to access the views
    permission_classes = (IsAuthenticated, )
    serializer_class = CSVDataSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        return CSVData.objects.filter(user=user) 

    def create(self, request) -> JsonResponse:
        return async_to_sync(self.create_data)(request)

    async def create_data(self, request):
        response = None

        user = request.user
        
        try:
            data = request.body.decode('utf-8')

            df = await asyncio.to_thread(pd.read_csv, StringIO(data))

            csv_dicts = df.to_dict('records')

            await self.save_csv_data_to_db(user, csv_dicts)

            response = JsonResponse({'message': 'CSV data uploaded successfully'})
        except Exception as exc:
            response = JsonResponse({"error_message": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return response

    async def save_csv_data_to_db(self, user: object, csv_dicts: list[dict[str, Any]]) -> NoReturn:
        loop = asyncio.get_event_loop()
        tasks = []
        for csv_dict in csv_dicts:
            csv_dict['user'] = user
            task = loop.create_task(sync_to_async(CSVData.objects.create)(**csv_dict))
            tasks.append(task)

        await asyncio.gather(*tasks) 
