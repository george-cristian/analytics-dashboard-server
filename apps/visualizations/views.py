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
from rest_framework import status, viewsets
from rest_framework.decorators import action
from django.contrib.auth.models import User
from rest_framework.mixins import (ListModelMixin, RetrieveModelMixin,
                                   UpdateModelMixin)

from .serializers import VisualizationSerializer
from .models import Visualization
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
        file_path = ""
        team = team.replace(" ", "_")
        if chart_type == 'line':
            file_path = await self.create_line_chart(user, team, team_df)
        elif chart_type == 'bar':
            file_path = await self.create_bar_chart(user, team, team_df)
        elif chart_type == 'scatter':
            file_path = await self.create_scatter_plot(user, team, team_df)

        return file_path

    async def create_line_chart(self, user, team, team_df):
        plt.figure(figsize=(20, 10))
        plt.plot(team_df.index, team_df['review_time'], label='Review Time')
        plt.plot(team_df.index, team_df['merge_time'], label='Merge Time')
        plt.xlabel('Date')
        plt.ylabel('Duration (s)')
        plt.title(f'{team} Review and Merge Times')
        plt.legend()
        plt.xticks(rotation=90)
        file_path = f'/visualizations/{user.id}/line/{team}_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        await self.save_plot(file_path)

        Visualization.objects.create(
            user=user,
            visualization_type='line',
            file_path=file_path,
            teams=[team],
        )

        return {'team': team,
                'file_path': file_path,
                'chart_type': 'line'}
    
    async def create_bar_chart(self, user, team, team_df):
        plt.figure(figsize=(20, 10))
        width = 0.35
        fig, ax = plt.subplots(figsize=(20, 10))
        
        # create a list of x positions for the bars
        x = np.arange(len(team_df))
        
        # plot review time and merge time as stacked bars
        rects1 = ax.bar(x, team_df['review_time'], width, label='Review Time')
        rects2 = ax.bar(x, team_df['merge_time'], width, bottom=team_df['review_time'], label='Merge Time')
        
        # set x-ticks to be the dates in the DataFrame
        ax.set_xticks(x)
        ax.set_xticklabels(team_df.index.strftime('%Y-%m-%d'), rotation=90)
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Duration (s)')
        ax.set_title(f'{team} Review and Merge Times')
        ax.legend()
        
        file_path = f'/visualizations/{user.id}/bar/{team}_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        await self.save_plot(file_path)

        Visualization.objects.create(
            user=user,
            visualization_type='bar',
            file_path=file_path,
            teams=[team],
        )

        return {'team': team,
                'file_path': file_path,
                'chart_type': 'bar'}

    async def create_scatter_plot(self, user, team, team_df):
        plt.figure(figsize=(20, 10))
        plt.scatter(team_df.index, team_df['review_time'], label='Review Time')
        plt.scatter(team_df.index, team_df['merge_time'], label='Merge Time')
        plt.xlabel('Date')
        plt.ylabel('Duration (s)')
        plt.title(f'{team} Review and Merge Times')
        plt.legend()
        plt.xticks(rotation=90)
        file_path = f'/visualizations/{user.id}/scatter/{team}_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        await self.save_plot(file_path)

        Visualization.objects.create(
            user=user,
            visualization_type='scatter',
            file_path=file_path,
            teams=[team],
        )

        return {'team': team,
                'file_path': file_path,
                'chart_type': 'scatter'}

    async def save_plot(self, file_path):
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Save the plot to the file path
        plt.savefig(file_path)

        # Clear the plot to free up memory
        plt.clf()
