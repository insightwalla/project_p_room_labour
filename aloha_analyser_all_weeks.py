import pandas as pd
import streamlit as st
import plotly.graph_objects as go

#st.stop()
def lambda_for_projecting_into_distribution(x, columns, column_to_multiply_for):
    '''
    columns: the columns to project into the distribution ('breakfast', 'lunch', 'afternoon', 'dinner')

    Example:
    x = data_breakfast.iloc[0]
    columns = breakfast_columns
    column_to_multiply_for = 'breakfast'

    x[7, 8, 9, 10, 11] = x[7, 8, 9, 10, 11] * x['breakfast'] (x['breakfast'] is the total for the breakfast covers)
    '''
    x[columns] = x[columns] * x[column_to_multiply_for]
    return x[columns]

def find_statistical_distribuition(data, columns_to_find_distribution):
    '''
    Example:
    We need to find the distribution of the breakfast covers in the hours columns.

    columns = |7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|23|
    columns_to_find_distribution = |7|8|9|10|11|
    daypart = 'breakfast'


    1. First find the total for the columns_to_find_distribution
    2. Divide each column by the total

    returns a dataframe with the distribution of the breakfast covers in the hours columns
    e.g.:

    '''
    # get the columns for the distribution
    data = data[columns_to_find_distribution]
    data['Total'] = data.sum(axis=1)
    data = data.div(data['Total'], axis=0)
    return data

def merge_with_projected_covers(data, daypart, covers_to_project):
    '''
    Here we merge the data with the projected covers.
    '''
    data.index.names = ['day']
    features = ['day'] + [daypart]
    covers = covers_to_project[features] 
    data = data.merge(covers, on='day')
    data.fillna(0, inplace=True)
    data.drop(columns=['Total'], inplace=True)
    return data

# final data for distribution
class TransformationAlohaData:
    '''
    Finding the Dishoom Birmingham distribution of a week in September 2022,
    and projecting the predicted covers for the week, to examine efficiency of the labour model.
    The final dataframe will have the days as rows and the hours as columns.

    '''
    def __init__(self, data_path, covers_to_project, plot = False):
        self.data_distribution = pd.read_csv(data_path)
        self.transform(covers_to_project)
        if plot:
            self.plot()

    def cleaning(self):
        '''
        Cleaning the data:
        '''
       
        # filter only the rows with the data that we can use
        # if void total and sales are == then drop the row
        self.data_distribution = self.data_distribution[self.data_distribution['Void_Total'] != self.data_distribution['Item_Sales']]
        self.data_distribution = self.data_distribution[(self.data_distribution['Guest_Count'] != 0) & (self.data_distribution['Item_Sales'] != 0)]
        # transform the date column in datetime
        self.data_distribution['Date'] = pd.to_datetime(self.data_distribution['Date'], format='%m-%d-%Y')
        # add month column  
        self.data_distribution['Month'] = self.data_distribution['Date'].dt.month
        # add dayname
        self.data_distribution['Day_Name'] = self.data_distribution['Date'].dt.day_name()
        # add week number
        self.data_distribution['Week_Number'] =self.data_distribution['Date'].dt.isocalendar().week
        #self.data_distribution = self.data_distribution[self.data_distribution['Week_Number'] == 37]
        # normalize the guest count if greater than 25 with dividing the sales by the sph set to 50 pp
        self.data_distribution['Guest_Count'] = self.data_distribution.apply(lambda x: x['Item_Sales'] / 30 if x['Guest_Count'] >= 25 else x['Guest_Count'], axis=1)
    
    def transformation0(self, store_name = 'D8 - Dishoom Birmingham', month = 9):
        '''
        We only considering the Dishoom Birmingham store, and the month of September 2022.
        But we can change the store and the month, to make the analysis for other stores and months.
        '''
        self.data_distribution = self.data_distribution[self.data_distribution['Store_Name'] == store_name]
        self.data_distribution = self.data_distribution[self.data_distribution['Month'] == month]
        self.possible_weeks = self.get_unique_weeks()
        #self.data_distribution = self.data_distribution[self.data_distribution['Week_Number'] == self.week_for_distribution]

    def transformation1(self):
        '''
        Here we are going to transform the Open_Time column, that contains the minutes after midnight,
        in a column with the real time of the check opening.
        '''
        self.data_distribution['Check_Hour'] = self.data_distribution['Open_Time'] / 60
        self.data_distribution['Check_Minutes'] = self.data_distribution['Open_Time'] % 60
        self.data_distribution['Check_Minutes'] = self.data_distribution['Check_Minutes'].astype(int)
        # if check minutes < 10, add a 0 before
        self.data_distribution['Check_Minutes'] = self.data_distribution['Check_Minutes'].apply(lambda x: f'0{x}' if x < 10 else x)
        self.data_distribution['Check_Time_Real'] = self.data_distribution['Check_Hour'].astype(int).astype(str) + ':' + self.data_distribution['Check_Minutes'].astype(str)
        self.data_distribution.drop(columns=['Check_Hour', 'Check_Minutes'], inplace=True)

    def transformation2(self):
        '''
        We created a new column with the real time of the check opening in the previous step.
        Now we can use this column to create a new column with the hour of the check opening.
        and preapare the dataframe for the heatmap.
        '''
        # keep columns Guest_Count, Check_Time_Real, Date
        self.data_distribution = self.data_distribution[['Guest_Count', 'Check_Time_Real', 'Date', 'Item_Sales', 'Day_Part_Name', 'Store_Name', 'Week_Number', 'Day_Name']]
        # create a hour column
        self.data_distribution['Hour'] = self.data_distribution['Check_Time_Real'].apply(lambda x: int(x.split(':')[0]))
        # change if hour == 0
        self.data_distribution['Hour'] = self.data_distribution['Hour'].apply(lambda x: 24 if x == 0 else x)        
        # divide by week 
    def transformation3(self):
        '''
        We can now group by dayname and hour and sum the guest count.
        Then we can create a new dataframe with the days as columns and the hours as rows.
        '''
        data_all_weeks = []
        for week in self.possible_weeks:
            data = self.data_distribution[self.data_distribution['Week_Number'] == week]
            data = data.groupby(['Day_Name', 'Hour']).sum(numeric_only=True).reset_index()
            # now pivot
            data = data.pivot(index='Hour', columns='Day_Name', values='Guest_Count')
            # now traspose because we want the days as rows and the hours as columns
            data = data.T
            # reindex the days
            data = data.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
            # add week number
            data['Week_Number'] = week
            # add to week dataframe
            data_all_weeks.append(data)
        # drop the week number column
        data_all_weeks = [data.drop(columns=['Week_Number']) for data in data_all_weeks]
        data_all_weeks = pd.concat(data_all_weeks).groupby(level=0).mean()

        # now traspose because we want the days as rows and the hours as columns
        self.data_distribution = data_all_weeks
        # reindex the days
        self.data_distribution = self.data_distribution.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])

        # setting up
                # columns for breakfast, Lunch, Afternoon, Dinner
        self.hours_columns = self.data_distribution.columns

        self.breakfast_columns = [col for col in self.hours_columns \
                    if col < 12]
        self.lunch_columns = [col for col in self.hours_columns \
                    if col >= 12 and col < 15]
        self.evening_columns = [col for col in self.hours_columns \
                    if col >= 15 and col < 18]
        self.dinner_columns = [col for col in self.hours_columns \
                    if col >= 18]

        self.dictionary_mapping = {
            'breakfast': self.breakfast_columns,
            'afternoon': self.lunch_columns,
            'evening': self.evening_columns,
            'dinner': self.dinner_columns
        }
        
    def transformation4(self, covers_to_project):
        data_breakfast = find_statistical_distribuition(self.data_distribution, columns_to_find_distribution = self.dictionary_mapping['breakfast'])
        data_lunch = find_statistical_distribuition(self.data_distribution, columns_to_find_distribution = self.dictionary_mapping['afternoon'])
        data_afternoon = find_statistical_distribuition(self.data_distribution, columns_to_find_distribution = self.dictionary_mapping['evening'])
        data_dinner = find_statistical_distribuition(self.data_distribution, columns_to_find_distribution = self.dictionary_mapping['dinner'])

        data_breakfast = merge_with_projected_covers(data_breakfast, daypart='breakfast', covers_to_project=covers_to_project)
        data_lunch = merge_with_projected_covers(data_lunch, daypart='afternoon', covers_to_project=covers_to_project)
        data_afternoon = merge_with_projected_covers(data_afternoon, daypart='evening', covers_to_project=covers_to_project)
        data_dinner = merge_with_projected_covers(data_dinner, daypart='dinner', covers_to_project=covers_to_project)

        data_breakfast[self.breakfast_columns] = data_breakfast.apply(lambda x: lambda_for_projecting_into_distribution(x, columns = self.breakfast_columns, column_to_multiply_for = 'breakfast'), axis=1)
        data_lunch[self.lunch_columns] = data_lunch.apply(lambda x: lambda_for_projecting_into_distribution(x, columns = self.lunch_columns, column_to_multiply_for = 'afternoon'), axis=1)
        data_afternoon[self.evening_columns] = data_afternoon.apply(lambda x: lambda_for_projecting_into_distribution(x, columns = self.evening_columns, column_to_multiply_for = 'evening'), axis=1)
        data_dinner[self.dinner_columns] = data_dinner.apply(lambda x: lambda_for_projecting_into_distribution(x, columns = self.dinner_columns, column_to_multiply_for = 'dinner'), axis=1)

        # merge in a single dataframe
        data_distribution = data_breakfast.merge(data_lunch, on='day').merge(data_afternoon, on='day').merge(data_dinner, on='day') 

        # drop the columns with the projected covers
        data_distribution.drop(columns=['breakfast', 'afternoon', 'evening', 'dinner'], inplace=True)
        data_distribution = data_distribution.round(0)
        data_distribution.index = data_distribution['day']
        data_distribution.drop(columns=['day'], inplace=True)
        self.data_distribution = data_distribution
        # all the columns are need to be :00
        self.data_distribution.columns = [f'{col}:00' if col < 24 else f'{col-24}:00' for col in self.data_distribution.columns]
    
    def transform(self, covers_to_project):
        self.cleaning()
        self.transformation0()
        self.transformation1()
        self.transformation2()
        self.transformation3()
        self.transformation4(covers_to_project)
        return self.data_distribution

    def plot(self):
        # create a heatmap
        fig = go.Figure(data=go.Heatmap(
                z=self.data_distribution,
                x=self.data_distribution.columns,
                y=self.data_distribution.index,
                hoverongaps = False,
                text = self.data_distribution,
                hovertemplate = 'Day: %{y}<br>Hour: %{x}<br>Number of people: %{z}<extra></extra>',
                textsrc='z', texttemplate='%{z}',
                colorscale='Blues',
                showscale=False,
                ))
        # plot
        fig.update_layout(
            title='Aloha Hours')
        st.plotly_chart(fig, use_container_width=True)

    def change_week_for_distribution(self, week_for_distribution):
        self.week_for_distribution = week_for_distribution
        self.transform()
        self.plot()

    def get_unique_weeks(self):
        return self.data_distribution['Week_Number'].unique()
    
if __name__ == '__main__':
    data_path = 'data/aloha.csv'
    covers_to_project = pd.read_csv('data/projected_med.csv')
    covers_to_project.columns = [col.strip() for col in covers_to_project.columns]

    transformation = TransformationAlohaData(data_path, covers_to_project, plot=True)
    