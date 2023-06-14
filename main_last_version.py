
'''
author: Roberto Scalas 
date:   2023-05-31 12:26:19.795742

This script is used to test the streamlit app.
To run it, type the following command in the terminal:

streamlit run main.py

'''
import pandas as pd
import streamlit as st
st.set_page_config(layout="wide")
import plotly.graph_objects as go

projected_covers_high = pd.read_csv('data/projected_high.csv')
projected_covers_low = pd.read_csv('data/projected_low.csv')
projected_covers_med = pd.read_csv('data/projected_med.csv')

with st.expander('Projected Covers'):
    c1,c2,c3 = st.columns(3)
    with c1:
        st.subheader('High')
        st.experimental_data_editor(projected_covers_high)
    with c3:
        st.subheader('Low')
        st.experimental_data_editor(projected_covers_low)
    with c2:
        st.subheader('Med')
        st.experimental_data_editor(projected_covers_med)


'''
This are the files containing the rota hours for each level of covers.
'''
data_high = pd.read_csv('data/rota_hours_high.csv')
data_low = pd.read_csv('data/rota_hours_low.csv')
data_med = pd.read_csv('data/rota_hours_med.csv')

'''Cleaning the data (We don't need to keep the shift that starts and ends in the same hour - empty or 0 hours)'''
# if start and end columns are equal, drop the row
data_high = data_high[data_high['Start Time (Hour)'] != data_high['End Time (Hour)']]
data_low = data_low[data_low['Start Time (Hour)'] != data_low['End Time (Hour)']]
data_med = data_med[data_med['Start Time (Hour)'] != data_med['End Time (Hour)']]

def plot_data(data_high):
    # add a hour start and hour end columns
    data_high['Start_Hour'] = data_high['Start Time (Hour)'].apply(lambda x: int(x.split(':')[0]))
    data_high['End_Hour'] = data_high['End Time (Hour)'].apply(lambda x: int(x.split(':')[0]))

    # is start > end? if yes, add 24 to end
    data_high['End_Hour'] = data_high.apply(lambda x: x['End_Hour'] + 24 if x['Start_Hour'] > x['End_Hour'] else x['End_Hour'], axis=1)
    #st.write(data_high)

    # get minimum start time and maximum end time
    min_start = data_high['Start_Hour'].min()
    max_end = data_high['End_Hour'].max()

    columns = range(min_start, max_end+1)
    # add columns to dataframe
    for col in columns:
        data_high[col] = 0

    # now populate the dataframe with 1 if the hour is between start and end
    for index, row in data_high.iterrows():
        for i in range(row['Start_Hour'], row['End_Hour']):
            data_high.at[index, i] = 1

    # keep only the columns with the hours

    # now create a dataframe with the total number for each hour
    data_high = data_high.groupby('Day').sum().reset_index()
    # set it as index
    data_high.set_index('Day', inplace=True)
    # reindex the order of the days
    data_high = data_high.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])

    # keep only columns with hours
    data_high = data_high[columns]
    # change columns names
    data_high.columns = [f'{col}:00' if col < 24 else f'{col-24}:00' for col in data_high.columns]
    #st.write(data_high)
    # create a heatmap
    fig = go.Figure(data=go.Heatmap(
                    z=data_high,
                    x=data_high.columns,
                    y=data_high.index,
                    hoverongaps = False,
                    text = data_high,
                    hovertemplate = 'Day: %{y}<br>Hour: %{x}<br>Number of people: %{z}<extra></extra>',
                    textsrc='z', texttemplate='%{z}',
                    colorscale='Blues',
                    showscale=False,
                    ))
    
    fig.update_layout(
        title='High',
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

    # create a chart for each day
    from plotly.subplots import make_subplots

    # create the figure
    fig = make_subplots(rows=7, cols=1, subplot_titles=data_high.index)
    for day in data_high.index:
        fig.add_trace(go.Line(x=data_high.columns, y=data_high.loc[day], name=day), row=data_high.index.get_loc(day)+1, col=1)

    fig.update_layout(height=1000, width=1000, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with st.expander('High'):
    plot_data(data_high)

with st.expander('Low'):
    plot_data(data_low)

with st.expander('Med'):
    plot_data(data_med)


# final data for distribution
data_distribution = pd.read_csv('data/aloha.csv')
data_distribution = data_distribution[data_distribution['Store_Name'] == 'D8 - Dishoom Birmingham']
data_distribution['Date'] = pd.to_datetime(data_distribution['Date'], format='%m-%d-%Y')
data_distribution['Month'] = data_distribution['Date'].dt.month
# keep only september
data_distribution = data_distribution[data_distribution['Month'] == 9]
# column 'Open_Time' contains minutes after midnight so divide by 60 to get hours
data_distribution['Check_Hour'] = data_distribution['Open_Time'] / 60
# use the remainder to get the minutes
data_distribution['Check_Minutes'] = data_distribution['Open_Time'] % 60
# transform the minutes in integer
data_distribution['Check_Minutes'] = data_distribution['Check_Minutes'].astype(int)
# if check minutes < 10, add a 0 before
data_distribution['Check_Minutes'] = data_distribution['Check_Minutes'].apply(lambda x: f'0{x}' if x < 10 else x)
# create a column with the time
data_distribution['Check_Time_Real'] = data_distribution['Check_Hour'].astype(int).astype(str) + ':' + data_distribution['Check_Minutes'].astype(str)
# drop the check hour and check minutes columns
data_distribution.drop(columns=['Check_Hour', 'Check_Minutes'], inplace=True)
# keep columns Guest_Count, Check_Time_Real, Date
data_distribution = data_distribution[['Guest_Count', 'Check_Time_Real', 'Date', 'Item_Sales', 'Day_Part_Name', 'Store_Name']]
# take off the rows that have 0 as both guest count and item sales
data_distribution = data_distribution[(data_distribution['Guest_Count'] != 0) & (data_distribution['Item_Sales'] != 0)]

# create a hour column
data_distribution['Hour'] = data_distribution['Check_Time_Real'].apply(lambda x: int(x.split(':')[0]))
# change if hour == 0
data_distribution['Hour'] = data_distribution['Hour'].apply(lambda x: 24 if x == 0 else x)

# add dayname
data_distribution['Day_Name'] = data_distribution['Date'].dt.day_name()

# add week number
data_distribution['Week_Number'] = data_distribution['Date'].dt.isocalendar().week

# only week 36
week_for_distribution = st.sidebar.selectbox('Select week', data_distribution['Week_Number'].unique(), index=1)
data_distribution = data_distribution[data_distribution['Week_Number'] == week_for_distribution]
#st.write(data_distribution)
# group by dayname and hour
data_distribution = data_distribution.groupby(['Day_Name', 'Hour']).sum(numeric_only=True).reset_index()

# now need to transform the dataframe in a format that can be used by the heatmap
# create a new dataframe with the days as columns and the hours as rows
data_distribution = data_distribution.pivot(index='Hour', columns='Day_Name', values='Guest_Count')
# now traspose
data_distribution = data_distribution.T
# reindex the days
data_distribution = data_distribution.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])

# create a heatmap
fig = go.Figure(data=go.Heatmap(
                z=data_distribution,
                x=data_distribution.columns,
                y=data_distribution.index,
                hoverongaps = False,
                text = data_distribution,
                hovertemplate = 'Day: %{y}<br>Hour: %{x}<br>Number of people: %{z}<extra></extra>',
                textsrc='z', texttemplate='%{z}',
                colorscale='Blues',
                showscale=False,
                ))
#st.plotly_chart(fig, use_container_width=True)


def lambda_for_regularization_breakfast(x, columns = [8, 9, 10, 11]):
    x[columns] = x[columns] * x[projected_covers_high.columns[1]]
    return x[columns]

def lambda_for_regularization_for_lunch(x, columns = [12, 13, 14]):
    x[columns] = x[columns] * x[projected_covers_high.columns[2]]
    return x[columns]

def lambda_for_regularization_for_afternoon(x, columns = [15, 16, 17]):
    x[columns] = x[columns] * x[projected_covers_high.columns[3]]
    return x[columns]

def lambda_for_regularization_for_dinner(x, columns = [18, 19, 20, 21, 22, 23]):
    x[columns] = x[columns] * x[projected_covers_high.columns[4]]
    return x[columns]

columns_breakfast = [8, 9, 10, 11]
columns_lunch = [12, 13, 14]
columns_afternoon = [15, 16, 17]
columns_dinner =  [18, 19, 20, 21, 22, 23]

# columns for breakfast, Lunch, Afternoon, Dinner
b_columns = [col for col in data_distribution.columns if col < 12]
l_columns = [col for col in data_distribution.columns if col >= 12 and col < 15]
a_columns = [col for col in data_distribution.columns if col >= 15 and col < 18]
d_columns = [col for col in data_distribution.columns if col >= 18]

breakfast_col_from_cover, lunch_col_from_cover, afternoon_col_from_cover, dinner_col_from_cover = projected_covers_high.columns[1], projected_covers_high.columns[2], projected_covers_high.columns[3], projected_covers_high.columns[4]

data_breakfast = data_distribution[b_columns] # filter only the columns for breakfast
data_breakfast['Breakfast_Total'] = data_breakfast.sum(axis=1) # sum the columns
data_breakfast = data_breakfast.div(data_breakfast['Breakfast_Total'], axis=0) # divide each column by the total
data_breakfast.drop(columns=['Breakfast_Total'], inplace=True) # drop the total column
data_breakfast.index.names = ['day'] # rename the index
features = ['day']+ [projected_covers_high.columns[1]] # get the right columns from the projected covers
covers = projected_covers_high[features] # get the projected covers
data_breakfast = data_breakfast.merge(covers, on='day')
data_breakfast.fillna(0, inplace=True)

data_lunch = data_distribution[l_columns]
data_lunch['Lunch_Total'] = data_lunch.sum(axis=1)
data_lunch = data_lunch.div(data_lunch['Lunch_Total'], axis=0)
data_lunch.drop(columns=['Lunch_Total'], inplace=True)
data_lunch.index.names = ['day']
features = ['day']+ [projected_covers_high.columns[2]]
covers = projected_covers_high[features]
data_lunch = data_lunch.merge(covers, on='day')
data_lunch.fillna(0, inplace=True)

data_afternoon = data_distribution[a_columns]
data_afternoon['Afternoon_Total'] = data_afternoon.sum(axis=1)
data_afternoon = data_afternoon.div(data_afternoon['Afternoon_Total'], axis=0)
data_afternoon.drop(columns=['Afternoon_Total'], inplace=True)
data_afternoon.index.names = ['day']
features = ['day']+ [projected_covers_high.columns[3]]
covers = projected_covers_high[features]
data_afternoon = data_afternoon.merge(covers, on='day')
data_afternoon.fillna(0, inplace=True)

data_dinner = data_distribution[d_columns]
data_dinner['Dinner_Total'] = data_dinner.sum(axis=1)
data_dinner = data_dinner.div(data_dinner['Dinner_Total'], axis=0)
data_dinner.drop(columns=['Dinner_Total'], inplace=True)
data_dinner.index.names = ['day']
features = ['day']+ [projected_covers_high.columns[4]]
covers = projected_covers_high[features]
data_dinner = data_dinner.merge(covers, on='day')
data_dinner.fillna(0, inplace=True)

data_breakfast[columns_breakfast] = data_breakfast.apply(lambda x: lambda_for_regularization_breakfast(x), axis=1)
#st.write(data_breakfast)
data_lunch[columns_lunch] = data_lunch.apply(lambda x: lambda_for_regularization_for_lunch(x), axis=1)
#st.write(data_lunch)
data_afternoon[columns_afternoon] = data_afternoon.apply(lambda x: lambda_for_regularization_for_afternoon(x), axis=1)
#st.write(data_afternoon)
data_dinner[columns_dinner] = data_dinner.apply(lambda x: lambda_for_regularization_for_dinner(x), axis=1)
#st.write(data_dinner)

# merge in a single dataframe
data_distribution = data_breakfast.merge(data_lunch, on='day')
data_distribution = data_distribution.merge(data_afternoon, on='day')
data_distribution = data_distribution.merge(data_dinner, on='day')

# drop the columns with the projected covers
data_distribution.drop(columns=[breakfast_col_from_cover, lunch_col_from_cover, afternoon_col_from_cover, dinner_col_from_cover], inplace=True)

# round all values to 0 decimals
data_distribution = data_distribution.round(0)
# set index to the day
data_distribution.index = data_distribution['day']
# drop the day column
data_distribution.drop(columns=['day'], inplace=True)
#st.write(data_distribution)

# create a heatmap
fig = go.Figure(data=go.Heatmap(
                z=data_distribution,
                x=data_distribution.columns,
                y=data_distribution.index,
                hoverongaps = False,
                text = data_distribution,
                hovertemplate = 'Day: %{y}<br>Hour: %{x}<br>Number of people: %{z}<extra></extra>',
                textsrc='z', texttemplate='%{z}',
                colorscale='Blues',
                showscale=False,
                ))
st.plotly_chart(fig, use_container_width=True)