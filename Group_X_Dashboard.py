"""
NYC Motor Vehicle Collisions - Interactive Dashboard
Group X Business Analytics Final Project
Phase 4: Dashboard Implementation
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

# ============================================================================
# DATA LOADING & PREPARATION
# ============================================================================

# Load the dataset
df = pd.read_csv('Motor_Vehicle_Collisions_Crashes.csv', low_memory=False)

# Data cleaning
df['CRASH DATE'] = pd.to_datetime(df['CRASH DATE'], format='%m/%d/%Y')
df['YEAR'] = df['CRASH DATE'].dt.year
df['MONTH'] = df['CRASH DATE'].dt.month
df['BOROUGH'] = df['BOROUGH'].fillna('UNKNOWN')
df['NUMBER OF PERSONS INJURED'] = df['NUMBER OF PERSONS INJURED'].fillna(0)
df['NUMBER OF PERSONS KILLED'] = df['NUMBER OF PERSONS KILLED'].fillna(0)

# Create injury type categorization
df['Primary_Injury_Type'] = 'None'
df.loc[df['NUMBER OF PEDESTRIANS INJURED'] > 0, 'Primary_Injury_Type'] = 'Pedestrian'
df.loc[df['NUMBER OF CYCLIST INJURED'] > 0, 'Primary_Injury_Type'] = 'Cyclist'
df.loc[df['NUMBER OF MOTORIST INJURED'] > 0, 'Primary_Injury_Type'] = 'Motorist'
df.loc[(df['NUMBER OF PEDESTRIANS INJURED'] > 0) & 
       (df['NUMBER OF MOTORIST INJURED'] > 0), 'Primary_Injury_Type'] = 'Pedestrian'

# Pre-calculate data for charts
annual_data = df.groupby('YEAR').agg({
    'COLLISION_ID': 'count',
    'NUMBER OF PERSONS INJURED': 'sum',
    'NUMBER OF PERSONS KILLED': 'sum'
}).rename(columns={'COLLISION_ID': 'Total_Collisions'}).reset_index()

borough_data = df[df['BOROUGH'] != 'UNKNOWN'].groupby('BOROUGH').agg({
    'COLLISION_ID': 'count',
    'NUMBER OF PERSONS INJURED': 'sum'
}).rename(columns={'COLLISION_ID': 'Collisions', 'NUMBER OF PERSONS INJURED': 'Injuries'}).reset_index()
borough_data['Injuries_per_Collision'] = (borough_data['Injuries'] / borough_data['Collisions']).round(2)
borough_data = borough_data.sort_values('Collisions', ascending=False)

# Top contributing factors
top_factors = df['CONTRIBUTING FACTOR VEHICLE 1'].value_counts().head(10).reset_index()
top_factors.columns = ['Factor', 'Count']

# ============================================================================
# INITIALIZE DASH APP
# ============================================================================

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define custom color scheme
colors = {
    'background': '#f8f9fa',
    'primary': '#003366',
    'secondary': '#0066cc',
    'success': '#28a745',
    'danger': '#dc3545',
    'warning': '#ffc107',
    'light': '#f8f9fa',
    'dark': '#343a40'
}

# ============================================================================
# DASHBOARD LAYOUT
# ============================================================================

app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("NYC Motor Vehicle Collisions Dashboard", 
                   className="text-center mb-2 mt-4", 
                   style={'color': colors['primary'], 'fontweight': 'bold'}),
            html.Hr(),
            html.P("Analyzing 12 years of NYC collision data (2013-2024) | Source: NYC Open Data",
                  className="text-center text-muted mb-4")
        ])
    ]),

    # Summary Cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Total Collisions", className="text-muted"),
                    html.H3(f"{len(df):,.0f}", style={'color': colors['primary']})
                ])
            ], className="shadow-sm")
        ], md=3, className="mb-3"),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Total Injured", className="text-muted"),
                    html.H3(f"{df['NUMBER OF PERSONS INJURED'].sum():,.0f}", 
                           style={'color': colors['danger']})
                ])
            ], className="shadow-sm")
        ], md=3, className="mb-3"),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Total Fatalities", className="text-muted"),
                    html.H3(f"{df['NUMBER OF PERSONS KILLED'].sum():,.0f}", 
                           style={'color': colors['danger']})
                ])
            ], className="shadow-sm")
        ], md=3, className="mb-3"),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Avg Injuries/Collision", className="text-muted"),
                    html.H3(f"{df['NUMBER OF PERSONS INJURED'].mean():.2f}", 
                           style={'color': colors['warning']})
                ])
            ], className="shadow-sm")
        ], md=3, className="mb-3"),
    ]),

    # Filtering Section
    dbc.Row([
        dbc.Col([
            html.Label("Filter by Borough:", className="fw-bold"),
            dcc.Dropdown(
                id='borough-filter',
                options=[{'label': 'All Boroughs', 'value': 'ALL'}] + 
                       [{'label': b, 'value': b} for b in sorted(df[df['BOROUGH'] != 'UNKNOWN']['BOROUGH'].unique())],
                value='ALL',
                className="mb-3"
            )
        ], md=4),
        
        dbc.Col([
            html.Label("Filter by Year Range:", className="fw-bold"),
            dcc.RangeSlider(
                id='year-filter',
                min=df['YEAR'].min(),
                max=df['YEAR'].max(),
                value=[df['YEAR'].min(), df['YEAR'].max()],
                marks={str(year): str(year) for year in range(df['YEAR'].min(), df['YEAR'].max() + 1, 2)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], md=8),
    ], className="mb-4 p-3 bg-light rounded"),

    # Chart Row 1: Trends & Borough Comparison
    dbc.Row([
        dbc.Col([
            dcc.Loading(
                id="loading-1",
                type="default",
                children=[
                    dcc.Graph(id='annual-trends-chart')
                ]
            )
        ], md=6),
        
        dbc.Col([
            dcc.Loading(
                id="loading-2",
                type="default",
                children=[
                    dcc.Graph(id='borough-comparison-chart')
                ]
            )
        ], md=6),
    ], className="mb-4"),

    # Chart Row 2: Injury Type Distribution & Contributing Factors
    dbc.Row([
        dbc.Col([
            dcc.Loading(
                id="loading-3",
                type="default",
                children=[
                    dcc.Graph(id='injury-type-chart')
                ]
            )
        ], md=6),
        
        dbc.Col([
            dcc.Loading(
                id="loading-4",
                type="default",
                children=[
                    dcc.Graph(id='contributing-factors-chart')
                ]
            )
        ], md=6),
    ], className="mb-4"),

    # Chart Row 3: Severity Heatmap & Temporal Pattern
    dbc.Row([
        dbc.Col([
            dcc.Loading(
                id="loading-5",
                type="default",
                children=[
                    dcc.Graph(id='monthly-heatmap-chart')
                ]
            )
        ], md=6),
        
        dbc.Col([
            dcc.Loading(
                id="loading-6",
                type="default",
                children=[
                    dcc.Graph(id='injury-severity-chart')
                ]
            )
        ], md=6),
    ], className="mb-4"),

    # Footer
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.P("Dashboard created for NYC Motor Vehicle Collisions Analysis | Group X Business Analytics Project",
                  className="text-center text-muted small")
        ])
    ]),

], fluid=True, style={'backgroundColor': colors['background']})

# ============================================================================
# CALLBACK FUNCTIONS FOR INTERACTIVITY
# ============================================================================

@app.callback(
    [Output('annual-trends-chart', 'figure'),
     Output('borough-comparison-chart', 'figure'),
     Output('injury-type-chart', 'figure'),
     Output('contributing-factors-chart', 'figure'),
     Output('monthly-heatmap-chart', 'figure'),
     Output('injury-severity-chart', 'figure')],
    [Input('borough-filter', 'value'),
     Input('year-filter', 'value')]
)
def update_charts(selected_borough, year_range):
    # Filter data based on selections
    filtered_df = df[(df['YEAR'] >= year_range[0]) & (df['YEAR'] <= year_range[1])].copy()
    
    if selected_borough != 'ALL':
        filtered_df = filtered_df[filtered_df['BOROUGH'] == selected_borough]
    
    # ========================================================================
    # Chart 1: Annual Trends (Q2)
    # ========================================================================
    annual_filtered = filtered_df.groupby('YEAR').agg({
        'COLLISION_ID': 'count',
        'NUMBER OF PERSONS INJURED': 'sum'
    }).rename(columns={'COLLISION_ID': 'Collisions', 'NUMBER OF PERSONS INJURED': 'Injuries'}).reset_index()
    
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig1.add_trace(
        go.Scatter(x=annual_filtered['YEAR'], y=annual_filtered['Collisions'],
                  name='Collisions', mode='lines+markers',
                  line=dict(color=colors['primary'], width=3),
                  marker=dict(size=8)),
        secondary_y=False
    )
    
    fig1.add_trace(
        go.Scatter(x=annual_filtered['YEAR'], y=annual_filtered['Injuries'],
                  name='Persons Injured', mode='lines+markers',
                  line=dict(color=colors['danger'], width=3),
                  marker=dict(size=8)),
        secondary_y=True
    )
    
    fig1.update_layout(
        title=f"Annual Collision & Injury Trends {year_range[0]}-{year_range[1]}",
        hovermode='x unified',
        template='plotly_white',
        font=dict(size=11)
    )
    fig1.update_xaxes(title_text="Year")
    fig1.update_yaxes(title_text="Number of Collisions", secondary_y=False)
    fig1.update_yaxes(title_text="Persons Injured", secondary_y=True)
    
    # ========================================================================
    # Chart 2: Borough Comparison (Q3)
    # ========================================================================
    borough_filtered = filtered_df[filtered_df['BOROUGH'] != 'UNKNOWN'].groupby('BOROUGH').agg({
        'COLLISION_ID': 'count',
        'NUMBER OF PERSONS INJURED': 'sum'
    }).rename(columns={'COLLISION_ID': 'Collisions'}).reset_index()
    borough_filtered = borough_filtered.sort_values('Collisions', ascending=True)
    
    fig2 = go.Figure(data=[
        go.Bar(x=borough_filtered['Collisions'], y=borough_filtered['BOROUGH'],
              orientation='h', marker=dict(color=colors['secondary']),
              text=borough_filtered['Collisions'], textposition='outside',
              hovertemplate='<b>%{y}</b><br>Collisions: %{x:,}<extra></extra>')
    ])
    
    fig2.update_layout(
        title="Collision Count by Borough",
        xaxis_title="Number of Collisions",
        yaxis_title="",
        template='plotly_white',
        showlegend=False,
        hovermode='y',
        font=dict(size=11)
    )
    
    # ========================================================================
    # Chart 3: Injury Type Distribution (Q3)
    # ========================================================================
    injury_type_dist = filtered_df['Primary_Injury_Type'].value_counts().reset_index()
    injury_type_dist.columns = ['Type', 'Count']
    injury_type_colors = {
        'None': '#d3d3d3',
        'Pedestrian': colors['danger'],
        'Cyclist': colors['warning'],
        'Motorist': colors['success']
    }
    
    fig3 = go.Figure(data=[
        go.Pie(labels=injury_type_dist['Type'], values=injury_type_dist['Count'],
               marker=dict(colors=[injury_type_colors.get(t, colors['light']) for t in injury_type_dist['Type']]),
               textposition='inside', textinfo='label+percent+value',
               hovertemplate='<b>%{label}</b><br>Count: %{value:,}<br>Percentage: %{percent}<extra></extra>')
    ])
    
    fig3.update_layout(
        title="Collision Distribution by Injury Type",
        template='plotly_white',
        font=dict(size=11),
        height=500
    )
    
    # ========================================================================
    # Chart 4: Top Contributing Factors (Q5)
    # ========================================================================
    top_factors_filtered = filtered_df['CONTRIBUTING FACTOR VEHICLE 1'].value_counts().head(10).reset_index()
    top_factors_filtered.columns = ['Factor', 'Count']
    top_factors_filtered = top_factors_filtered.sort_values('Count', ascending=True)
    
    fig4 = go.Figure(data=[
        go.Bar(x=top_factors_filtered['Count'], y=top_factors_filtered['Factor'],
              orientation='h', marker=dict(color=colors['primary']),
              text=top_factors_filtered['Count'], textposition='outside',
              hovertemplate='<b>%{y}</b><br>Incidents: %{x:,}<extra></extra>')
    ])
    
    fig4.update_layout(
        title="Top 10 Contributing Factors to Collisions",
        xaxis_title="Number of Incidents",
        yaxis_title="",
        template='plotly_white',
        showlegend=False,
        hovermode='y',
        font=dict(size=10)
    )
    
    # ========================================================================
    # Chart 5: Monthly Heatmap (Seasonal Pattern)
    # ========================================================================
    monthly_data = filtered_df.groupby(['YEAR', 'MONTH']).agg({
        'COLLISION_ID': 'count'
    }).rename(columns={'COLLISION_ID': 'Collisions'}).reset_index()
    
    # Create pivot table for heatmap
    heatmap_data = monthly_data.pivot(index='MONTH', columns='YEAR', values='Collisions')
    
    fig5 = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        colorscale='YlOrRd',
        colorbar=dict(title="Collisions"),
        hovertemplate='<b>%{y} %{x}</b><br>Collisions: %{z:,.0f}<extra></extra>'
    ))
    
    fig5.update_layout(
        title="Monthly Collision Patterns (Seasonal Heatmap)",
        xaxis_title="Year",
        yaxis_title="Month",
        template='plotly_white',
        font=dict(size=11)
    )
    
    # ========================================================================
    # Chart 6: Injury Severity Distribution
    # ========================================================================
    severity_data = filtered_df['NUMBER OF PERSONS INJURED'].value_counts().head(10).sort_index()
    
    fig6 = go.Figure(data=[
        go.Bar(x=severity_data.index, y=severity_data.values,
              marker=dict(color=severity_data.values, colorscale='Reds'),
              text=severity_data.values, textposition='outside',
              hovertemplate='<b>%{x} Persons Injured</b><br>Incidents: %{y:,}<extra></extra>')
    ])
    
    fig6.update_layout(
        title="Distribution of Injury Severity (Top 10)",
        xaxis_title="Number of Persons Injured per Incident",
        yaxis_title="Number of Incidents",
        template='plotly_white',
        showlegend=False,
        font=dict(size=11),
        hovermode='x'
    )
    
    return fig1, fig2, fig3, fig4, fig5, fig6

# ============================================================================
# RUN THE APP
# ============================================================================

if __name__ == '__main__':
    app.run(debug=False, port=8050)
