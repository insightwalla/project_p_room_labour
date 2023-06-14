
'''
author: Roberto Scalas 
date:   2023-05-31 12:26:19.795742

This script is used to test the streamlit app.
To run it, type the following command in the terminal:

streamlit run main.py

'''
import streamlit as st
st.set_page_config(layout="wide")
import pandas as pd
import plotly.graph_objects as go

def plotting_both_heatmap(heatmap1, heatmap2):
    # if all columns are int then pass else:
    if not all(isinstance(col, int) for col in heatmap1.data_distribution.columns):
        # change columns to int taking off the last ':00'
        heatmap1.data_distribution.columns = [int(col[:-3]) for col in heatmap1.data_distribution.columns]
        heatmap1.data_distribution.columns = [col+24 if col < 7 else col for col in heatmap1.data_distribution.columns]
        heatmap1.data_distribution = heatmap1.data_distribution.sort_index(axis=1)

    if not all(isinstance(col, int) for col in heatmap2.data.columns):
        # change columns to int taking off the last ':00'
        heatmap2.data.columns = [int(col[:-3]) for col in heatmap2.data.columns]
        heatmap2.data.columns = [col+24 if col < 7 else col for col in heatmap2.data.columns]
        heatmap2.data = heatmap2.data.sort_index(axis=1)

    new_heatmap = heatmap1.data_distribution/heatmap2.data
    fig = go.Figure(data=go.Heatmap(
            z= new_heatmap,
            x= [str(col)+':00' if col < 24 else str(col-24)+':00' for col in new_heatmap.columns], 
            y=new_heatmap.index,
            hoverongaps = False,
            text = new_heatmap,
            hovertemplate = 'Day: %{y} <br> Hour: %{x}<br>Ratio (Covers / Employees): %{z}<extra></extra>',
            # round the text to 2 decimal places
            textsrc='z', texttemplate='%{text:.2f}',
            colorscale='Blues',
            showscale=False,
            ))
    # add title
    fig.update_layout(
        title='Ratio (Covers / Employees)')

    # plot
    st.plotly_chart(fig, use_container_width=True)
    # no nan values 0 instead
    new_heatmap = new_heatmap.fillna(0)

    #st.write(new_heatmap)


    from plotly.subplots import make_subplots
    # make subplot with seconsday y axis with plotly 
    fig = make_subplots(rows=7, cols=1, subplot_titles=heatmap1.data_distribution.index, shared_xaxes=True, vertical_spacing=0.02, specs=[[{"secondary_y": True}]]*7)
    for day in heatmap1.data_distribution.index:
        fig.add_trace(go.Line(
            x=heatmap2.data.columns, 
            y=heatmap2.data.loc[day], 
            name='Rota Hours',
            # add hover text
            hovertemplate = 'Hour: %{x}:00 <br>Rota Hours: %{y}<extra></extra>',
            #fill = 'tozeroy',
            ),
            row = heatmap2.data.index.get_loc(day)+1,
            col=1, 
            secondary_y = False) # add hover text
        
        fig.add_trace(go.Line(
            x=heatmap1.data_distribution.columns,
            y=heatmap1.data_distribution.loc[day],
            name='Covers',
            # add hover text
            hovertemplate = 'Hour: %{x}:00 <br>Covers: %{y}<extra></extra>', 
            #fill = 'tozeroy',
  
            ),
            row=heatmap1.data_distribution.index.get_loc(day)+1,
            col=1, # add hover text
            secondary_y=False,
            )
        
        fig.add_trace(go.Bar(
            x=new_heatmap.columns,
            y=new_heatmap.loc[day],
            name='Ratio (Covers/Employees)', opacity=0.5,
            # add hover text
            hovertemplate = 'Hour: %{x}:00 <br>Ratio (Covers / Employees): %{y}<extra></extra>',
            ),
            row=new_heatmap.index.get_loc(day)+1,
            col=1, # add hover text
            secondary_y=True,
            )
        
    # set title
    fig.update_layout(title='Day by day comparison')
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


from rota_models_analyser import TransformationRotaHours
from aloha_analyser_all_weeks import TransformationAlohaData

projected_delivery = pd.read_csv('data/delivery_sales.csv')
spo = 38.99
projected_delivery = projected_delivery.div(spo)
projected_delivery = projected_delivery.astype(int)

projected_covers_high = pd.read_csv('data/projected_high.csv')
projected_covers_low = pd.read_csv('data/projected_low.csv')
projected_covers_med = pd.read_csv('data/projected_med.csv')
# no spaces in columns
projected_covers_high.columns = [col.strip() for col in projected_covers_high.columns]
projected_covers_low.columns = [col.strip() for col in projected_covers_low.columns]
projected_covers_med.columns = [col.strip() for col in projected_covers_med.columns]


def merge_with_delivery_distributed(projected_covers_high, level='high_delivery'):
    '''
    The logic is the following:
    1. Sum all the projected covers in breakfast, afternoon, evening and dinner for each day
        Now we can get the weekly distribution of covers
    2. Divide each projected covers by the total number of covers
        to get the weekly distribution
    3. Now I need to find the day_part distribution for each day 
        (breakfast, afternoon, evening, dinner)
    
    '''
    columns = ['breakfast', 'afternoon', 'evening', 'dinner']
    projected_covers_high['Total_summed'] = projected_covers_high[columns].sum(axis=1)
    total_covers = projected_covers_high['Total_summed'].sum()
    projected_covers_high['weekly_distribution'] = projected_covers_high['Total_summed'].div(total_covers)
    projected_covers_high['Total_Cover_Delivery_Distributed'] = projected_covers_high['weekly_distribution'].apply(lambda x: int(x*projected_delivery[level]))
    
    columns = ['breakfast', 'afternoon', 'evening', 'dinner']
    for col in columns:
        projected_covers_high[col] = projected_covers_high[col].div(projected_covers_high['Total_summed'])
    
    projected_covers_high['Total_summed'] = projected_covers_high['Total_Cover_Delivery_Distributed'] + projected_covers_high['Total_summed']
    for col in columns:
        projected_covers_high[col] = projected_covers_high[col].mul(projected_covers_high['Total_summed'])

    projected_covers_high[columns] = projected_covers_high[columns].astype(int)
    projected_covers_high = projected_covers_high.drop(columns=['Total_summed', 'weekly_distribution', 'Total_Cover_Delivery_Distributed'])
    return projected_covers_high

if st.checkbox('with delivery sales'):
    projected_covers_high = merge_with_delivery_distributed(projected_covers_high, level = 'high_delivery')
    projected_covers_med = merge_with_delivery_distributed(projected_covers_med, level = 'med_delivery')
    projected_covers_low = merge_with_delivery_distributed(projected_covers_low, level = 'low_delivery')

data_path_high = pd.read_csv('data/rota_hours_high.csv')
data_path_med = pd.read_csv('data/rota_hours_med.csv')
data_path_low = pd.read_csv('data/rota_hours_low.csv')
# no space in columns
data_path_high.columns = [col.strip() for col in data_path_high.columns]
data_path_med.columns = [col.strip() for col in data_path_med.columns]
data_path_low.columns = [col.strip() for col in data_path_low.columns]

with st.expander('Shift FOH'):
    c1,c2,c3 = st.columns(3)
    projected_covers_high = c1.experimental_data_editor(projected_covers_high, use_container_width=True, key='high')
    projected_covers_low = c2.experimental_data_editor(projected_covers_low, use_container_width=True, key='low')
    projected_covers_med = c3.experimental_data_editor(projected_covers_med, use_container_width=True, key='med')
    
    data_path_high = c1.experimental_data_editor(data_path_high, use_container_width=True, key='high_1')
    data_path_med = c2.experimental_data_editor(data_path_med, use_container_width=True, key='med_1')
    data_path_low = c3.experimental_data_editor(data_path_low, use_container_width=True, key='low_1')

list_of_roles = list(data_path_high['Role'].unique())
role = st.multiselect('Select role', list_of_roles)
if role:
    # filter the dataframe
    data_path_high = data_path_high[data_path_high['Role'].isin(role)]
    data_path_med = data_path_med[data_path_med['Role'].isin(role)]
    data_path_low = data_path_low[data_path_low['Role'].isin(role)]
    
#transformation_high = TransformationAlohaData('data/aloha.csv', projected_covers_high)
#unique_weeks = list(transformation_high.possible_weeks) + ['All']
#week_to_analyse = st.selectbox('Select week to analyse', unique_weeks)

c1,c2,c3 = st.columns(3)
with c1.expander('High'):
    transformation_high = TransformationAlohaData(
            'data/aloha.csv',
            projected_covers_high,
            plot = True
            )
    transformed_rota_hours_high = TransformationRotaHours(data_path = data_path_high)
    transformed_rota_hours_high.transform()
    transformed_rota_hours_high.plot()
    plotting_both_heatmap(heatmap1=transformation_high, heatmap2=transformed_rota_hours_high)

with c3.expander('Low'):
    transformation_low = TransformationAlohaData(
            'data/aloha.csv', 
            projected_covers_low,
            plot = True
            )
    transformed_rota_hours_low = TransformationRotaHours(data_path=data_path_low)
    transformed_rota_hours_low.transform()
    transformed_rota_hours_low.plot()

    plotting_both_heatmap(heatmap1=transformation_low, heatmap2=transformed_rota_hours_low)

with c2.expander('Med'):
    transformation_med = TransformationAlohaData(
        'data/aloha.csv',
        projected_covers_med,
        plot = True
        )

    transformed_rota_hours_med = TransformationRotaHours(data_path=data_path_med)
    transformed_rota_hours_med.transform()
    transformed_rota_hours_med.plot()

    plotting_both_heatmap(heatmap1=transformation_med, heatmap2=transformed_rota_hours_med)
