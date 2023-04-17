import asyncio
import traceback
from io import StringIO
from typing import Any, Dict, Any, Union

import numpy as np
import pandas as pd
from asgiref.sync import async_to_sync, sync_to_async
from django.http import JsonResponse, HttpRequest
from rest_framework import status, viewsets
from rest_framework.mixins import (ListModelMixin, RetrieveModelMixin,
                                   UpdateModelMixin)
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import QuerySet

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

    def get_queryset(self) -> QuerySet[CSVData]:
        user = self.request.user
        return CSVData.objects.filter(user=user) 

    def create(self, request: HttpRequest) -> JsonResponse:
        return async_to_sync(self.create_data)(request)

    async def create_data(self, request: HttpRequest) -> JsonResponse:
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

    async def save_csv_data_to_db(self, user: object, csv_dicts: list[dict[str, Any]]) -> None:
        loop = asyncio.get_event_loop()
        tasks = []
        for csv_dict in csv_dicts:
            csv_dict['user'] = user
            task = loop.create_task(sync_to_async(CSVData.objects.create)(**csv_dict))
            tasks.append(task)

        await asyncio.gather(*tasks)

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request: HttpRequest) -> JsonResponse:
        return async_to_sync(self.get_statistics)(request)
    
    async def get_statistics(self, request) -> JsonResponse:
        user = request.user
        team = request.query_params.get('team')
        
        csv_data = await sync_to_async(CSVData.objects.filter)(user=user)

        csv_data = csv_data.values_list('review_time', 'merge_time', 'team')
        df = pd.DataFrame(csv_data, columns=['review_time', 'merge_time', 'team'])
        df = df.astype({'review_time': int, 'merge_time': int})

        if team is not None:
            df = df[df['team'] == team]

        if df.empty:
            return JsonResponse({'error': 'No data available for the specified team.'}, status=status.HTTP_404_NOT_FOUND)
        
        team_stats = self.calculate_team_stats(df)

        return JsonResponse(team_stats, status=status.HTTP_200_OK)

    def calculate_team_stats(self, df: pd.DataFrame) -> dict[str, dict[str, dict[str, Union[float, int]]]]:
        team_stats = {}

        for team, team_df in df.groupby('team'):
            team_stats[team] = {
                'review_time': self.calculate_single_statistics(team_df, 'review_time'),
                'merge_time': self.calculate_single_statistics(team_df, 'merge_time')
            }

        return team_stats

    def calculate_single_statistics(self, team_df: pd.DataFrame, col_type: str) -> dict[str, Union[float, int]]:
        time_mean = np.mean(team_df[col_type])
        time_median = np.median(team_df[col_type])
        time_mode = int(team_df[col_type].mode().iloc[0])

        return {
            'mean': time_mean,
            'median': time_median,
            'mode': time_mode
        }

    