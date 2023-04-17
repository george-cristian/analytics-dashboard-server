import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

FILE_URL_PREFIX = "http://127.0.0.1:8000"

class PlottingHandler:
    
    @staticmethod
    async def create_chart(chart_type: str, file_path: str, team: str, team_df: pd.DataFrame) -> None:
        if chart_type == 'line':
            await PlottingHandler.create_line_chart(file_path, team, team_df)
        elif chart_type == 'bar':
            await PlottingHandler.create_bar_chart(file_path, team, team_df)
        elif chart_type == 'scatter':
            await PlottingHandler.create_scatter_plot(file_path, team, team_df)

    @staticmethod
    async def create_line_chart(file_path: str, team: str, team_df: pd.DataFrame) -> None:
        plt.figure(figsize=(20, 10))

        plt.plot(team_df.index, team_df['review_time'], label='Review Time')
        plt.plot(team_df.index, team_df['merge_time'], label='Merge Time')

        plt.xlabel('Date')
        plt.ylabel('Duration (s)')
        plt.title(f'{team} Review and Merge Times')
        plt.legend()
        plt.xticks(rotation=90)

        await PlottingHandler.save_plot(file_path)
    
    @staticmethod
    async def create_bar_chart(file_path: str, team: str, team_df: pd.DataFrame) -> None:
        plt.figure(figsize=(20, 10))

        width = 0.35
        fig, ax = plt.subplots(figsize=(20, 10))
        
        # create a list of x positions for the bars
        x = np.arange(len(team_df))
        
        # plot review time and merge time as stacked bars
        rects1 = ax.bar(x, team_df['review_time'], width, label='Review Time')
        rects2 = ax.bar(x, team_df['merge_time'], width, bottom=team_df['review_time'], label='Merge Time')
        
        # set x labels to be the dates in the DataFrame
        ax.set_xticks(x)
        ax.set_xticklabels(team_df.index.strftime('%Y-%m-%d'), rotation=90)
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Duration (s)')
        ax.set_title(f'{team} Review and Merge Times')
        ax.legend()
        
        await PlottingHandler.save_plot(file_path)

    @staticmethod
    async def create_scatter_plot(file_path: str, team: str, team_df: pd.DataFrame) -> None:
        plt.figure(figsize=(20, 10))

        plt.scatter(team_df.index, team_df['review_time'], label='Review Time')
        plt.scatter(team_df.index, team_df['merge_time'], label='Merge Time')

        plt.xlabel('Date')
        plt.ylabel('Duration (s)')
        plt.title(f'{team} Review and Merge Times')
        plt.legend()
        plt.xticks(rotation=90)

        await PlottingHandler.save_plot(file_path)

    @staticmethod
    async def save_plot(file_path: str) -> None:
        # create the directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # save the plot to the file path
        plt.savefig(file_path)

        # clear the plot
        plt.clf()
