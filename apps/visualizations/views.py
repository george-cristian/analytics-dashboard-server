from datetime import datetime
import os
import asyncio

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from asgiref.sync import async_to_sync, sync_to_async
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from django.contrib.auth.models import User
from rest_framework.mixins import (ListModelMixin, RetrieveModelMixin,
                                   UpdateModelMixin)

from .serializers import VisualizationSerializer
from .models import Visualization
from .utils import PlottingHandler, FILE_URL_PREFIX
from apps.csvdata.models import CSVData


class VisualizationViewSet(ListModelMixin,
                  RetrieveModelMixin,
                  UpdateModelMixin,
                  viewsets.GenericViewSet):
    
    # allow only authenticated users to access the views
    permission_classes = (IsAuthenticated, )
    serializer_class = VisualizationSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        return Visualization.objects.filter(user=user)

    def create(self, request):
        return async_to_sync(self.create_plots)(request)
    
    async def create_plots(self, request):
        user = request.user

        team = request.query_params.get('team')
        chart_type = request.query_params.get('type')

        csv_data = await sync_to_async(CSVData.objects.filter)(user=user)

        chart_types = []
        if chart_type is not None:
            chart_types.append(chart_type)
        else:
            chart_types = ['line', 'bar', 'scatter']

        csv_data = csv_data.values_list('review_time', 'merge_time', 'date', 'team')
        df = pd.DataFrame(csv_data, columns=['review_time', 'merge_time', 'date', 'team'])
        df = df.astype({'review_time': int, 'merge_time': int})

        if team is not None:
            df = df[df['team'] == team]

        if df.empty:
            return JsonResponse({'error': 'No data available for the specified team.'}, status=status.HTTP_404_NOT_FOUND)
        tasks = []
        for team, team_df in df.groupby('team'):
            # Convert date strings to datetime objects and set them as the index
            team_df['date'] = pd.to_datetime(team_df['date'])
            team_df = team_df.set_index('date')

            # Resample the data to a daily frequency and interpolate missing values
            team_df = team_df.resample('D').mean()
            team_df = team_df.interpolate()

            for chart_type in chart_types:
                task = asyncio.ensure_future(self.create_chart(user, team, team_df, chart_type))
                tasks.append(task)

        file_paths = await asyncio.gather(*tasks)

        return JsonResponse({'message': 'Charts generated successfully.',
                             'paths': file_paths})
    
    @action(detail=False, methods=['get', 'post'], url_path='share')
    def share(self, request):
        if request.method == 'POST':
            return self.share_with_user(request)
        else:
            return self.get_shared_visualizations(request)
            
    def share_with_user(self, request):
        response = None
        try:
            username = request.query_params.get('username', None)
            shared_with = get_object_or_404(User, username=username)
            visualizations = Visualization.objects.filter(user=request.user)
            for visualization in visualizations:
                visualization.shared_with.add(shared_with)
            response = JsonResponse({'message': 'Charts have been shared successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            response = JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return response

    def get_shared_visualizations(self, request):
        response = None
        try:
            user = request.user
            shared_visualizations = Visualization.objects.filter(shared_with=user)
            serializer = VisualizationSerializer(shared_visualizations, many=True)
            response = JsonResponse(serializer.data, safe=False)
        except Exception as exc:
            response = JsonResponse({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return response

    async def create_chart(self, user, team, team_df, chart_type):
        file_path = f'/visualizations/{user.id}/{chart_type}/{team}_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'

        file_url = FILE_URL_PREFIX + file_path
        
        team = team.replace(" ", "_")

        await PlottingHandler.create_chart(chart_type, file_path, team, team_df)

        await self.create_visualization_in_db(user, chart_type, file_path, team)

        return {'team': team,
                'file_url': file_url,
                'chart_type': 'line'}
    
    @sync_to_async
    def create_visualization_in_db(self, user, chart_type, file_path, team):
        Visualization.objects.create(
            user=user,
            visualization_type=chart_type,
            file_path=file_path,
            teams=[team],
        )

