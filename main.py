import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import networkx
import networkx as nx
from plotly.offline import download_plotlyjs, init_notebook_mode,  iplot, plot
from dash.dependencies import Input, Output
from datetime import datetime
import data_processing
from IPython.display import display, HTML
import numpy as np
import plotly.graph_objs as go

# global variables

df_full = data_processing.getFullTable()
df_rssi = data_processing.rssiDataFrame(df_full)



def make_annotations(Xn,Yn, anno_text, font_size=11, font_color='rgb(10,10,10)'):
    L=len(Xn)
    if len(anno_text)!=L:
        raise ValueError('The lists pos and text must have the same len')
    annotations = []
    for k in range(L):
        annotations.append(dict(text=anno_text[k],
                                x=Xn[k],
                                y=Yn[k],
                                xref='x1', yref='y1',
                                font=dict(color= font_color, size=font_size),
                                showarrow=False)
                          )
    return annotations

def myGraph(df, sensor_name):

    init_notebook_mode(connected=True)

    receiver_id = df[df['sensors'] == sensor_name]['receiverid'].unique()

    G_sensors = nx.Graph()
    G_sensors.add_nodes_from(range(len(receiver_id)))
    G_sensors.add_edges_from([])

    # layouts correspond to the spatial position of nodes
    # pos_sensors = nx.fruchterman_reingold_layout(G_sensors)

    labels = receiver_id
    labels_rssi = data_processing.rssiMinMaxToString(df, sensor_name)

    #Xn_sensors = [pos_sensors[k][0] for k in range(len(pos_sensors))]
    #Yn_sensors = [pos_sensors[k][1] for k in range(len(pos_sensors))]

    Yn_sensors = receiver_id
    Xn_sensors = [sensor_name]* len(receiver_id)
    trace_nodes = dict(type='scatter',
                       x=Xn_sensors,
                       y=Yn_sensors,
                       mode='markers',
                       marker=dict(symbol='circle-dot', size=70, color='rgb(0,240,0)'),
                       text=labels_rssi,
                       hoverinfo='text',
                       name='all_nodes')

    trace_edges = dict(type='scatter',
                       mode='lines',
                       x=[],
                       y=[],
                       line=dict(width=1, color='rgb(25,25,25)'),
                       hoverinfo='none'
                       )

    x_axis = dict(showline=False,  # hide axis line, grid, ticklabels and  title
                  zeroline=False,
                  showgrid=False,
                  showticklabels=False,  # print out values on the axis
                  title='receiver id'
                  )

    y_axis = dict(showline=False,
                  zeroline=False,
                  showgrid=False,
                  showticklabels=False,
                  title=''
                  )

    layout = dict(title='Sensor '+ sensor_name,
                  font=dict(family='Balto'),
                  width=400,
                  height=500,
                  autosize=False,
                  showlegend=False,
                  xaxis=x_axis,
                  yaxis=y_axis,
                  margin=dict(
                      l=40,
                      r=40,
                      b=85,
                      t=100,
                      pad=0,),
                  hovermode='closest',
                  plot_bgcolor='#efecea',  # set background color
                  )

    fig = dict(data=[trace_edges, trace_nodes], layout=layout)
    fig['layout'].update(annotations=make_annotations(Xn_sensors, Yn_sensors, labels))
    return fig


def plotRSSI(df, sensor_name, receiver_name):

    init_notebook_mode(connected=True)

    df_small = df[(df['sensors'] == sensor_name) & (df['receiverid']==receiver_name)].reset_index()
    df_small = df_small.sort_values(['timestamp'])
    df_small['seconds'] = (df_small['timestamp'] - df_small['timestamp'].min()).round()

    Xn = df_small['seconds'].values
    Yn = df_small['message_payload_rssi'].values


    trace= dict(type = 'scatter',
                x=Xn,
                y=Yn,
                mode='lines + markers',
                #marker=dict(symbol='circle-dot', size=100, color='rgb(0,240,0)'),
                line = dict(
                    color = ('rgb(244, 98, 66)'),
                    width = 1,),
                )


    x_axis = dict(showline=False,
                  zeroline=False,
                  showgrid=True,
                  showticklabels=True,
                  title='time in sec'
                  )

    y_axis = dict(showline=False,
                  zeroline=False,
                  showgrid=True,
                  showticklabels=True,
                  title='rssi'
                  )

    layout = dict(title='Sensor ' + sensor_name+' receiver '+receiver_name,
                  width=600,
                  height=400,
                  margin = {'l': 40, 'b': 40, 'r': 10, 't': 50},
                  autosize=False,
                  showlegend=False,
                  xaxis=x_axis,
                  yaxis=y_axis,
                  hovermode='closest',
                  plot_bgcolor='#efecea',  # set background color
                  )

    fig = dict(data=[trace], layout=layout)
    return fig


######################################################
#                 application form                   #
######################################################
app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1(
        children='blik.',
        style={
            'textAlign': 'center',
            'color': 'rgb(3, 160, 165)'}
    ),
    html.P('The change of the RSSI value for each sensor unit at every receiver over time. '
           'RSSI - received signal strength indicator.', style={'textAlign': 'center', 'color': 'rgb(3, 160, 165)',}),

    html.Div([
        dcc.Graph(
             id='graph_sensors',
             figure=myGraph(df_rssi, '01-003-0014'),
             hoverData={'points': [3, 3]}
            )], style={'width': '30%', 'display': 'inline-block', 'vertical-align': 'top'}),
    html.Div(children=
    [
        html.P('Please, choose the sensor_id.', style={ 'font-style': 'italic', 'color':'rgb(115, 116, 119)',}),
        dcc.Dropdown(
            id='sensor_id_dropdown',
            options=[{'label': i, 'value': i} for i in sorted(df_rssi['sensors'].unique())],
            value='01-003-0014',
        ),

        html.P('Please, move a mouse onto the circle on the graph to see corresponding time and the signal plot.', style={
            'font-style': 'italic',
            'color':'rgb(115, 116, 119)',}
               ),
        html.P('The time range the sensor was sending its message to a receiver:'),
        html.Div(id='output_time_range', style={'font-style': 'bold'}),
        html.P(" "),
        #html.P("The sensor's message was captured but this receiver for such amount of time:"),
        html.Div(id='output_time_difference', style={'font-style': 'bold'}),

        dcc.Graph(
            id='graph_rssi',
            figure=plotRSSI(df_full, '01-003-0014', '02-004-0000'),
            # hoverData={'points': [3, 3]}
        ),

    ], style={'width': '45%', 'display': 'inline-block', 'vertical-align': 'middle', 'horizontal-align':'left'})
])


@app.callback(
    dash.dependencies.Output(component_id='graph_sensors', component_property = 'figure'),
    [dash.dependencies.Input(component_id='sensor_id_dropdown',component_property= 'value')])
def update_graph_sensor(sensor_name):
    return(myGraph(df_rssi, sensor_name))

@app.callback(
    dash.dependencies.Output('output_time_range', 'children'),
    [dash.dependencies.Input('graph_sensors', 'hoverData')])
def update_time_range(hoverData):
    sensor_name = hoverData['points'][0]['x']
    receiver_name = hoverData['points'][0]['y']
    df_small = df_rssi[(df_rssi['sensors']== sensor_name) & (df_rssi['receiverid'] == receiver_name)].reset_index()
    start, end = df_small['time_std_min'][0], df_small['time_std_max'][0]
    return('from {0} to {1}'.format(start[0:len(start)], end[0:len(end)])) # 11


@app.callback(
    dash.dependencies.Output('output_time_difference', 'children'),
    [dash.dependencies.Input('graph_sensors', 'hoverData')])
def update_time_difference(hoverData):
    sensor_name = hoverData['points'][0]['x']
    receiver_name = hoverData['points'][0]['y']
    df_small = df_rssi[(df_rssi['sensors']== sensor_name) & (df_rssi['receiverid'] == receiver_name)].reset_index()
    return('difference: {0}'.format(df_small['time_diff'][0]))

@app.callback(
        dash.dependencies.Output('graph_rssi', 'figure'),
        [dash.dependencies.Input('graph_sensors', 'hoverData')])
def update_graph_rssi(hoverData):
    sensor_name = hoverData['points'][0]['x']
    receiver_name = hoverData['points'][0]['y']
    return plotRSSI(df_full, sensor_name,receiver_name)


if __name__ == '__main__':
    app.run_server()
