import pandas as pd
import streamlit as st
import plotly.graph_objects as go

class TransformationRotaHours:
    def __init__(self, data_path = 'data/rota_hours_high.csv'):
        '''
        The data contains a start time and end time for each shift. 
        We need to transform this data to a format that we can use to plot a heatmap and a chart.
        '''
        if type(data_path) == str:
            self.data = pd.read_csv(data_path)
        else:
            self.data = data_path

    def cleaning(self):
        '''Cleaning the data (We don't need to keep the shift that starts and ends in the same hour - empty or 0 hours)'''
        # if start and end columns are equal, drop the row
        self.data = self.data[self.data['Start Time (Hour)'] != self.data['End Time (Hour)']]
        # add a hour start and hour end columns
        self.data['Start_Hour'] = self.data['Start Time (Hour)'].apply(lambda x: int(x.split(':')[0]))
        self.data['End_Hour'] = self.data['End Time (Hour)'].apply(lambda x: int(x.split(':')[0]))
        # is start > end? if yes, add 24 to end
        self.data['End_Hour'] = self.data.apply(lambda x: x['End_Hour'] + 24 if x['Start_Hour'] > x['End_Hour'] else x['End_Hour'], axis=1)
        #st.write(self.data)

    def transformation0(self):
        '''
        Creating the hours columns and populating them with 1 if the hour is between start and end
        '''
        # get minimum start time and maximum end time
        min_start = self.data['Start_Hour'].min()
        max_end = self.data['End_Hour'].max()

        self.columns_hours = range(min_start, max_end+1)
        
        # add columns to dataframe and initialize with 0
        for col in self.columns_hours:
            self.data[col] = 0

        # now populate the dataframe with 1 if the hour is between start and end
        for index, row in self.data.iterrows():
            for hour in range(row['Start_Hour'], row['End_Hour']):
                self.data.at[index, hour] = 1

    def transformation1(self):
        '''
        Here we are going to apply the groupby function to get the total number of people for each hour.
        and prepare the dataframe for the heatmap and the charts.
        1. Groupby day and sum the hours so we get the total number of people for each day
        '''
        # now create a dataframe with the total number for each hour
        self.data = self.data.groupby('Day').sum().reset_index()
        # set it as index
        self.data.set_index('Day', inplace=True)
        # reindex the order of the days
        self.data = self.data.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
        # keep only columns with hours
        self.data = self.data[self.columns_hours]
        # change columns names
        self.data.columns = [f'{col}:00' if col < 24 else f'{col-24}:00' for col in self.data.columns]
        #st.write(self.data)

    def transform(self):
        self.cleaning()
        self.transformation0()
        self.transformation1()
        return self.data
    
    def plot(self):
        # create a heatmap
        fig = go.Figure(data=go.Heatmap(
                        z=self.data,
                        x=self.data.columns,
                        y=self.data.index,
                        hoverongaps = False,
                        text = self.data,
                        hovertemplate = 'Day: %{y}<br>Hour: %{x}<br>Number of people: %{z}<extra></extra>',
                        textsrc='z', texttemplate='%{z}',
                        colorscale='Blues',
                        showscale=False,
                        ))
        
        fig.update_layout(
            title='Rotas Hours',
            xaxis_nticks=24,
            xaxis_title='Hour',
            yaxis_title='Day',
            yaxis_nticks=7,
            width=1000,
            height=500,
        )

        # no colorbar
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    def plot_1(self):
        # create a chart for each day
        from plotly.subplots import make_subplots

        # create the figure
        fig = make_subplots(rows=7, cols=1, subplot_titles=self.data.index)
        for day in self.data.index:
            fig.add_trace(go.Line(x=self.data.columns, y=self.data.loc[day], name=day), row=self.data.index.get_loc(day)+1, col=1)

        fig.update_layout(height=1000, width=1000, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


if __name__ == '__main__':
    transformation = TransformationRotaHours(data_path='data/rota_hours_high.csv')
    transformation.transform()
    transformation.plot()
