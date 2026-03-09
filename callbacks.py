from dash import Input, Output, State, dcc, html
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import io
import base64

def register_callbacks(app, df):
    
    # ============================================================================
    # CALLBACK 1 : INITIALISER LES DROPDOWNS
    # ============================================================================
    @app.callback(
        [Output('dept-filter', 'options'),
         Output('disease-filter', 'options'),
         Output('treatment-filter', 'options')],
        Input('dept-filter', 'id')
    )
    def initialize_dropdowns(_):
        dept_options = [{'label': dept, 'value': dept} for dept in sorted(df['Departement'].unique())]
        disease_options = [{'label': disease, 'value': disease} for disease in sorted(df['Maladie'].unique())]
        treatment_options = [{'label': treatment, 'value': treatment} for treatment in sorted(df['Traitement'].unique())]
        
        return dept_options, disease_options, treatment_options
    
    # ============================================================================
    # CALLBACK 2 : RÉINITIALISER LES FILTRES
    # ============================================================================
    @app.callback(
        [Output('dept-filter', 'value'),
         Output('disease-filter', 'value'),
         Output('treatment-filter', 'value'),
         Output('age-filter', 'value')],
        Input('reset-filters', 'n_clicks'),
        prevent_initial_call=True
    )
    def reset_filters(n_clicks):
        return None, None, None, [0, 100]
    
    # ============================================================================
    # FONCTION : GÉNÉRER DES INSIGHTS AUTOMATIQUES
    # ============================================================================
    def generate_insights(filtered_df, df_full):
        insights = []
        
        # Insight 1 : Comparaison avec dataset complet
        if len(filtered_df) < len(df_full):
            percentage = (len(filtered_df) / len(df_full)) * 100
            insights.append({
                'type': 'info',
                'icon': 'fas fa-filter',
                'title': 'Sélection active',
                'text': f"Vous analysez {len(filtered_df)} patients ({percentage:.1f}% du total)"
            })
        
        # Insight 2 : Coût élevé
        avg_cost = filtered_df['Cout'].mean()
        overall_avg = df_full['Cout'].mean()
        diff_cost = ((avg_cost - overall_avg) / overall_avg) * 100
        
        if abs(diff_cost) > 10:
            if diff_cost > 0:
                insights.append({
                    'type': 'warning',
                    'icon': 'fas fa-exclamation-triangle',
                    'title': '⚠️ Coûts élevés',
                    'text': f"Le coût moyen est {abs(diff_cost):.1f}% supérieur à la moyenne générale ({avg_cost:,.0f}€ vs {overall_avg:,.0f}€)"
                })
            else:
                insights.append({
                    'type': 'success',
                    'icon': 'fas fa-check-circle',
                    'title': '✅ Coûts optimisés',
                    'text': f"Le coût moyen est {abs(diff_cost):.1f}% inférieur à la moyenne ({avg_cost:,.0f}€ vs {overall_avg:,.0f}€)"
                })
        
        # Insight 3 : Durée de séjour
        avg_duration = filtered_df['DureeSejour'].mean()
        overall_duration = df_full['DureeSejour'].mean()
        diff_duration = ((avg_duration - overall_duration) / overall_duration) * 100
        
        if abs(diff_duration) > 15:
            if diff_duration > 0:
                insights.append({
                    'type': 'warning',
                    'icon': 'fas fa-clock',
                    'title': '⏱️ Séjours prolongés',
                    'text': f"La durée moyenne est {abs(diff_duration):.1f}% plus longue ({avg_duration:.1f} jours vs {overall_duration:.1f} jours)"
                })
            else:
                insights.append({
                    'type': 'success',
                    'icon': 'fas fa-check-circle',
                    'title': '✅ Séjours courts',
                    'text': f"La durée moyenne est {abs(diff_duration):.1f}% plus courte ({avg_duration:.1f} jours)"
                })
        
        # Insight 4 : Pathologie dominante
        if len(filtered_df) > 0:
            top_disease = filtered_df['Maladie'].value_counts().iloc[0]
            top_disease_name = filtered_df['Maladie'].value_counts().index[0]
            disease_pct = (top_disease / len(filtered_df)) * 100
            
            if disease_pct > 30:
                insights.append({
                    'type': 'info',
                    'icon': 'fas fa-disease',
                    'title': f'🏥 Pathologie dominante : {top_disease_name}',
                    'text': f"Représente {disease_pct:.1f}% des cas ({top_disease} patients)"
                })
        
        # Insight 5 : Profil d'âge
        age_60_plus = len(filtered_df[filtered_df['Age'] >= 60])
        if age_60_plus > 0:
            age_60_pct = (age_60_plus / len(filtered_df)) * 100
            if age_60_pct > 50:
                insights.append({
                    'type': 'info',
                    'icon': 'fas fa-user-friends',
                    'title': '👴 Population âgée dominante',
                    'text': f"{age_60_pct:.1f}% des patients ont 60 ans ou plus ({age_60_plus} patients)"
                })
        
        # Insight 6 : Recommandation basée sur les données
        if avg_duration > 8 and avg_cost > 4000:
            insights.append({
                'type': 'primary',
                'icon': 'fas fa-lightbulb',
                'title': '💡 RECOMMANDATION',
                'text': "Durée et coûts élevés : Envisager des protocoles de sortie précoce ou hospitalisation à domicile"
            })
        
        # Insight 7 : Top département
        if len(filtered_df) > 0:
            top_dept = filtered_df['Departement'].value_counts().iloc[0]
            top_dept_name = filtered_df['Departement'].value_counts().index[0]
            dept_pct = (top_dept / len(filtered_df)) * 100
            
            if dept_pct > 25:
                insights.append({
                    'type': 'info',
                    'icon': 'fas fa-hospital',
                    'title': f'🏥 Département le plus sollicité : {top_dept_name}',
                    'text': f"{dept_pct:.1f}% des admissions ({top_dept} patients)"
                })
        
        return insights
    
    # ============================================================================
    # CALLBACK 3 : DASHBOARD PRINCIPAL + INSIGHTS
    # ============================================================================
    @app.callback(
        [Output('total-patients', 'children'),
         Output('avg-duration', 'children'),
         Output('avg-cost', 'children'),
         Output('total-cost', 'children'),
         Output('trend-patients', 'children'),
         Output('trend-duration', 'children'),
         Output('trend-cost', 'children'),
         Output('trend-total', 'children'),
         Output('insights-content', 'children'),
         Output('dept-chart', 'figure'),
         Output('disease-chart', 'figure'),
         Output('treatment-cost-chart', 'figure'),
         Output('duration-disease-chart', 'figure'),
         Output('age-gender-chart', 'figure'),
         Output('monthly-admissions-chart', 'figure'),
         Output('cost-duration-scatter', 'figure'),
         Output('admission-vs-sortie-chart', 'figure'),
         Output('sortie-weekday-chart', 'figure')],
        [Input('dept-filter', 'value'),
         Input('disease-filter', 'value'),
         Input('treatment-filter', 'value'),
         Input('age-filter', 'value')]
    )
    def update_dashboard(dept_values, disease_values, treatment_values, age_range):
        # Filtrer les données
        filtered_df = df.copy()
        
        if dept_values:
            filtered_df = filtered_df[filtered_df['Departement'].isin(dept_values)]
        
        if disease_values:
            filtered_df = filtered_df[filtered_df['Maladie'].isin(disease_values)]
        
        if treatment_values:
            filtered_df = filtered_df[filtered_df['Traitement'].isin(treatment_values)]
        
        if age_range:
            filtered_df = filtered_df[(filtered_df['Age'] >= age_range[0]) & 
                                     (filtered_df['Age'] <= age_range[1])]
        
        # KPIs
        total_patients = f"{len(filtered_df):,}"
        avg_duration = f"{filtered_df['DureeSejour'].mean():.1f}"
        avg_cost = f"{filtered_df['Cout'].mean():,.0f}"
        total_cost = f"{filtered_df['Cout'].sum():,.0f}"
        
        # Tendances (comparaison avec dataset complet)
        trend_patients = ""
        trend_duration = ""
        trend_cost = ""
        trend_total = ""
        
        if len(filtered_df) < len(df):
            pct = (len(filtered_df) / len(df)) * 100
            trend_patients = f"📊 {pct:.0f}% du total"
            
            avg_dur_filtered = filtered_df['DureeSejour'].mean()
            avg_dur_full = df['DureeSejour'].mean()
            diff_dur = ((avg_dur_filtered - avg_dur_full) / avg_dur_full) * 100
            if diff_dur > 0:
                trend_duration = f"↗️ +{diff_dur:.0f}% vs moyenne"
            else:
                trend_duration = f"↘️ {diff_dur:.0f}% vs moyenne"
            
            avg_cost_filtered = filtered_df['Cout'].mean()
            avg_cost_full = df['Cout'].mean()
            diff_cost = ((avg_cost_filtered - avg_cost_full) / avg_cost_full) * 100
            if diff_cost > 0:
                trend_cost = f"↗️ +{diff_cost:.0f}% vs moyenne"
            else:
                trend_cost = f"↘️ {diff_cost:.0f}% vs moyenne"
            
            total_cost_filtered = filtered_df['Cout'].sum()
            total_cost_full = df['Cout'].sum()
            pct_total = (total_cost_filtered / total_cost_full) * 100
            trend_total = f"📊 {pct_total:.0f}% du total"
        
        # Générer les insights
        insights = generate_insights(filtered_df, df)
        insights_html = []
        
        if insights:
            for insight in insights:
                color_map = {
                    'success': 'success',
                    'warning': 'warning',
                    'info': 'info',
                    'primary': 'primary'
                }
                color = color_map.get(insight['type'], 'secondary')
                
                insights_html.append(
                    html.Div([
                        html.I(className=f"{insight['icon']} me-2"),
                        html.Strong(insight['title'] + ": ", className='me-1'),
                        html.Span(insight['text'])
                    ], className=f'alert alert-{color} mb-2')
                )
        else:
            insights_html = [html.P("Aucun insight particulier pour cette sélection.", 
                                   className='text-muted text-center')]
        
        # Palette Clinique Naturelle — Vert forêt · Or boisé · Sage · Argile
        color_palette = ['#0E6B45', '#B8860B', '#4A7C59', '#8B4513', '#1A8055',
                        '#E8A320', '#6B9E78', '#A0522D', '#0B4D32', '#D4A843']
        
        # Graphiques (code identique à avant)
        # 1. Département
        dept_data = filtered_df['Departement'].value_counts().reset_index()
        dept_data.columns = ['Departement', 'Count']
        
        fig_dept = px.bar(
            dept_data,
            x='Departement',
            y='Count',
            color='Departement',
            color_discrete_sequence=color_palette,
            title=""
        )
        fig_dept.update_layout(
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#3D5247', size=12),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#E8E0D5'),
            margin=dict(l=20, r=20, t=20, b=20),
            height=300
        )
        fig_dept.update_traces(hovertemplate='<b>%{x}</b><br>Patients: %{y}<extra></extra>')
        
        # 2. Pathologie
        disease_data = filtered_df['Maladie'].value_counts().reset_index()
        disease_data.columns = ['Maladie', 'Count']
        
        fig_disease = px.pie(
            disease_data,
            names='Maladie',
            values='Count',
            hole=0.5,
            color_discrete_sequence=color_palette,
            title=""
        )
        fig_disease.update_layout(
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#3D5247', size=12),
            margin=dict(l=20, r=20, t=20, b=20),
            height=300
        )
        fig_disease.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Patients: %{value}<br>Pourcentage: %{percent}<extra></extra>'
        )
        
        # 3. Coût par traitement
        treatment_cost = filtered_df.groupby('Traitement')['Cout'].mean().reset_index()
        treatment_cost = treatment_cost.sort_values('Cout', ascending=True)
        
        fig_treatment = px.bar(
            treatment_cost,
            y='Traitement',
            x='Cout',
            orientation='h',
            color='Cout',
            color_continuous_scale='Viridis',
            title=""
        )
        fig_treatment.update_layout(
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#3D5247', size=12),
            xaxis=dict(showgrid=True, gridcolor='#E8E0D5', title='Coût Moyen (€)'),
            yaxis=dict(showgrid=False, title=''),
            margin=dict(l=20, r=20, t=20, b=20),
            height=300
        )
        fig_treatment.update_traces(hovertemplate='<b>%{y}</b><br>Coût moyen: %{x:,.0f}€<extra></extra>')
        
        # 4. Durée par pathologie
        duration_disease = filtered_df.groupby('Maladie')['DureeSejour'].mean().reset_index()
        duration_disease = duration_disease.sort_values('DureeSejour', ascending=False)
        
        fig_duration = px.bar(
            duration_disease,
            x='Maladie',
            y='DureeSejour',
            color='DureeSejour',
            color_continuous_scale='RdYlGn_r',
            title=""
        )
        fig_duration.update_layout(
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#3D5247', size=12),
            xaxis=dict(showgrid=False, title=''),
            yaxis=dict(showgrid=True, gridcolor='#E8E0D5', title='Durée Moyenne (jours)'),
            margin=dict(l=20, r=20, t=20, b=20),
            height=300
        )
        fig_duration.update_traces(hovertemplate='<b>%{x}</b><br>Durée moyenne: %{y:.1f} jours<extra></extra>')
        
        # 5. Âge et sexe
        fig_age_gender = px.histogram(
            filtered_df,
            x='Age',
            color='Sexe',
            nbins=20,
            color_discrete_map={'M': '#0E6B45', 'F': '#B8860B'},
            title=""
        )
        fig_age_gender.update_layout(
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#3D5247', size=12),
            xaxis=dict(showgrid=False, title='Âge'),
            yaxis=dict(showgrid=True, gridcolor='#E8E0D5', title='Nombre de patients'),
            legend=dict(title='Sexe', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=20, r=20, t=40, b=20),
            height=300,
            barmode='group'
        )
        
        # 6. Évolution mensuelle
        filtered_df['Mois'] = filtered_df['DateAdmission'].dt.to_period('M').astype(str)
        monthly_data = filtered_df.groupby('Mois').size().reset_index(name='Admissions')
        
        fig_monthly = px.line(
            monthly_data,
            x='Mois',
            y='Admissions',
            markers=True,
            title=""
        )
        fig_monthly.update_traces(
            line_color='#0E6B45',
            line_width=3,
            marker=dict(size=8, color='#B8860B'),
            hovertemplate='<b>%{x}</b><br>Admissions: %{y}<extra></extra>'
        )
        fig_monthly.update_layout(
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#3D5247', size=12),
            xaxis=dict(showgrid=False, title='Mois'),
            yaxis=dict(showgrid=True, gridcolor='#E8E0D5', title="Nombre d'admissions"),
            margin=dict(l=20, r=20, t=20, b=20),
            height=300
        )
        
        # 7. Scatter Coût vs Durée
        fig_scatter = px.scatter(
            filtered_df,
            x='DureeSejour',
            y='Cout',
            color='Departement',
            size='Age',
            hover_data=['Maladie', 'Traitement', 'Age', 'Sexe'],
            color_discrete_sequence=color_palette,
            title=""
        )
        fig_scatter.update_layout(
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#3D5247', size=12),
            xaxis=dict(showgrid=True, gridcolor='#E8E0D5', title='Durée de Séjour (jours)'),
            yaxis=dict(showgrid=True, gridcolor='#E8E0D5', title='Coût (€)'),
            legend=dict(title='Département', orientation='v'),
            margin=dict(l=20, r=20, t=20, b=20),
            height=400
        )
        
        # 8. Flux Admissions vs Sorties
        filtered_df['MoisAdmission'] = filtered_df['DateAdmission'].dt.to_period('M').astype(str)
        filtered_df['MoisSortie'] = filtered_df['DateSortie'].dt.to_period('M').astype(str)
        
        admissions_monthly = filtered_df.groupby('MoisAdmission').size().reset_index(name='Admissions')
        sorties_monthly = filtered_df.groupby('MoisSortie').size().reset_index(name='Sorties')
        
        admissions_monthly.columns = ['Mois', 'Admissions']
        sorties_monthly.columns = ['Mois', 'Sorties']
        
        flux_data = admissions_monthly.merge(sorties_monthly, on='Mois', how='outer').fillna(0)
        
        fig_flux = go.Figure()
        fig_flux.add_trace(go.Scatter(
            x=flux_data['Mois'],
            y=flux_data['Admissions'],
            mode='lines+markers',
            name='Admissions',
            line=dict(color='#0E6B45', width=3),
            marker=dict(size=8, color='#0E6B45')
        ))
        fig_flux.add_trace(go.Scatter(
            x=flux_data['Mois'],
            y=flux_data['Sorties'],
            mode='lines+markers',
            name='Sorties',
            line=dict(color='#B8860B', width=3),
            marker=dict(size=8, color='#B8860B')
        ))
        
        fig_flux.update_layout(
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#3D5247', size=12),
            xaxis=dict(showgrid=False, title='Mois'),
            yaxis=dict(showgrid=True, gridcolor='#E8E0D5', title='Nombre de patients'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=20, r=20, t=40, b=20),
            height=300,
            hovermode='x unified'
        )
        
        # 9. Jours de sortie
        filtered_df['JourSortie'] = filtered_df['DateSortie'].dt.day_name()
        
        jours_ordre = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        jours_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        
        sortie_weekday = filtered_df['JourSortie'].value_counts().reindex(jours_ordre, fill_value=0).reset_index()
        sortie_weekday.columns = ['Jour', 'Count']
        sortie_weekday['JourFR'] = jours_fr
        
        fig_weekday = px.bar(
            sortie_weekday,
            x='JourFR',
            y='Count',
            color='Count',
            color_continuous_scale='Viridis',
            title=""
        )
        fig_weekday.update_layout(
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#3D5247', size=12),
            xaxis=dict(showgrid=False, title='Jour de la semaine'),
            yaxis=dict(showgrid=True, gridcolor='#E8E0D5', title='Nombre de sorties'),
            margin=dict(l=20, r=20, t=20, b=20),
            height=300
        )
        fig_weekday.update_traces(hovertemplate='<b>%{x}</b><br>Sorties: %{y}<extra></extra>')
        
        return (total_patients, avg_duration, avg_cost, total_cost,
                trend_patients, trend_duration, trend_cost, trend_total,
                insights_html,
                fig_dept, fig_disease, fig_treatment, fig_duration,
                fig_age_gender, fig_monthly, fig_scatter, fig_flux, fig_weekday)
    
    # ============================================================================
    # CALLBACK 4 : TÉLÉCHARGER EXCEL
    # ============================================================================
    @app.callback(
        Output("download-excel", "data"),
        Input("btn-download-excel", "n_clicks"),
        [State('dept-filter', 'value'),
         State('disease-filter', 'value'),
         State('treatment-filter', 'value'),
         State('age-filter', 'value')],
        prevent_initial_call=True
    )
    def download_excel(n_clicks, dept_values, disease_values, treatment_values, age_range):
        # Filtrer les données
        filtered_df = df.copy()
        
        if dept_values:
            filtered_df = filtered_df[filtered_df['Departement'].isin(dept_values)]
        
        if disease_values:
            filtered_df = filtered_df[filtered_df['Maladie'].isin(disease_values)]
        
        if treatment_values:
            filtered_df = filtered_df[filtered_df['Traitement'].isin(treatment_values)]
        
        if age_range:
            filtered_df = filtered_df[(filtered_df['Age'] >= age_range[0]) & 
                                     (filtered_df['Age'] <= age_range[1])]
        
        # Créer un buffer en mémoire
        output = io.BytesIO()
        
        # Créer le fichier Excel avec pandas
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            filtered_df.to_excel(writer, sheet_name='Données', index=False)
            
            # Créer une feuille de statistiques
            stats_df = pd.DataFrame({
                'Indicateur': ['Nombre de patients', 'Durée moyenne (jours)', 'Coût moyen (€)', 'Coût total (€)'],
                'Valeur': [
                    len(filtered_df),
                    f"{filtered_df['DureeSejour'].mean():.1f}",
                    f"{filtered_df['Cout'].mean():,.0f}",
                    f"{filtered_df['Cout'].sum():,.0f}"
                ]
            })
            stats_df.to_excel(writer, sheet_name='Statistiques', index=False)
        
        output.seek(0)
        
        return dcc.send_bytes(output.getvalue(), 
                             f"hospital_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
    
    # ============================================================================
    # CALLBACK 5 : TÉLÉCHARGER HTML
    # ============================================================================
    @app.callback(
        Output("download-html", "data"),
        Input("btn-download-html", "n_clicks"),
        [State('dept-filter', 'value'),
         State('disease-filter', 'value'),
         State('treatment-filter', 'value'),
         State('age-filter', 'value')],
        prevent_initial_call=True
    )
    def download_html(n_clicks, dept_values, disease_values, treatment_values, age_range):
        # Filtrer les données
        filtered_df = df.copy()
        
        if dept_values:
            filtered_df = filtered_df[filtered_df['Departement'].isin(dept_values)]
        
        if disease_values:
            filtered_df = filtered_df[filtered_df['Maladie'].isin(disease_values)]
        
        if treatment_values:
            filtered_df = filtered_df[filtered_df['Traitement'].isin(treatment_values)]
        
        if age_range:
            filtered_df = filtered_df[(filtered_df['Age'] >= age_range[0]) & 
                                     (filtered_df['Age'] <= age_range[1])]
        
        # Générer statistiques
        # Calculs pour le rapport
        top_dept = filtered_df['Departement'].value_counts().index[0] if len(filtered_df) > 0 else "—"
        top_disease = filtered_df['Maladie'].value_counts().index[0] if len(filtered_df) > 0 else "—"
        dept_stats = filtered_df.groupby('Departement').agg(
            Patients=('PatientID','count'),
            Cout_Moyen=('Cout','mean'),
            Duree_Moy=('DureeSejour','mean')
        ).reset_index().sort_values('Patients', ascending=False)

        dept_rows = ""
        for _, row in dept_stats.iterrows():
            dept_rows += f"""
            <tr>
                <td><strong>{row['Departement']}</strong></td>
                <td style="text-align:center">{int(row['Patients'])}</td>
                <td style="text-align:center">{row['Cout_Moyen']:,.0f} €</td>
                <td style="text-align:center">{row['Duree_Moy']:.1f} j</td>
            </tr>"""

        stats_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rapport DATA CARE — {datetime.now().strftime('%d/%m/%Y')}</title>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;0,700;1,400&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --forest:   #0B4D32;
      --forest2:  #0E6B45;
      --gold:     #B8860B;
      --gold2:    #E8A320;
      --clay:     #8B4513;
      --sage:     #4A7C59;
      --ivory:    #F7F3EE;
      --ivory2:   #EDE7DC;
      --border:   #D4C9BB;
      --text:     #1C2820;
      --textm:    #7A9080;
    }}
    *, *::before, *::after {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{
      font-family: 'Outfit', sans-serif;
      background: var(--ivory);
      color: var(--text);
      min-height: 100vh;
    }}

    /* ── HEADER ── */
    .report-header {{
      background: var(--forest);
      padding: 48px 60px 40px;
      position: relative;
      overflow: hidden;
    }}
    .report-header::before {{
      content: '';
      position: absolute;
      right: -60px; top: -60px;
      width: 280px; height: 280px;
      border-radius: 50%;
      background: rgba(184,134,11,0.08);
    }}
    .report-header::after {{
      content: '';
      position: absolute;
      right: 80px; top: -90px;
      width: 180px; height: 180px;
      border-radius: 50%;
      background: rgba(232,163,32,0.05);
    }}
    .header-badge {{
      display: inline-block;
      background: rgba(255,255,255,0.10);
      border: 1px solid rgba(255,255,255,0.15);
      color: rgba(255,255,255,0.70);
      font-size: 11px; font-weight: 700;
      letter-spacing: 2px; text-transform: uppercase;
      padding: 5px 14px; border-radius: 20px;
      margin-bottom: 18px;
    }}
    .report-title {{
      font-family: 'Cormorant Garamond', serif;
      font-size: 52px; font-weight: 700;
      color: white; line-height: 1;
      margin-bottom: 10px;
    }}
    .report-title em {{ font-style: italic; color: var(--gold2); }}
    .report-subtitle {{
      font-size: 13px; color: rgba(255,255,255,0.50);
      text-transform: uppercase; letter-spacing: 1.5px;
      font-weight: 400; margin-bottom: 6px;
    }}
    .report-date {{
      font-size: 13px; color: rgba(255,255,255,0.40);
      font-weight: 300;
    }}

    /* ── BODY ── */
    .report-body {{ padding: 40px 60px 60px; max-width: 1100px; margin: 0 auto; }}

    /* ── KPIs ── */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 18px;
      margin: 36px 0;
    }}
    .kpi-card {{
      background: white;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 22px 18px;
      position: relative;
      overflow: hidden;
      box-shadow: 0 2px 16px rgba(11,77,50,0.07);
      transition: all .25s;
    }}
    .kpi-card::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
    }}
    .kpi-card:hover {{ box-shadow: 0 6px 28px rgba(11,77,50,0.13); }}
    .kpi-card.k1::before {{ background: var(--forest2); }}
    .kpi-card.k2::before {{ background: var(--gold); }}
    .kpi-card.k3::before {{ background: var(--sage); }}
    .kpi-card.k4::before {{ background: var(--clay); }}
    .kpi-val {{
      font-size: 30px; font-weight: 700;
      line-height: 1; letter-spacing: -0.5px;
    }}
    .kpi-card.k1 .kpi-val {{ color: var(--forest); }}
    .kpi-card.k2 .kpi-val {{ color: var(--gold); }}
    .kpi-card.k3 .kpi-val {{ color: var(--sage); }}
    .kpi-card.k4 .kpi-val {{ color: var(--clay); }}
    .kpi-lbl {{
      font-size: 10px; font-weight: 700;
      text-transform: uppercase; letter-spacing: 1px;
      color: var(--textm); margin-top: 6px;
    }}

    /* ── SECTION TITLE ── */
    .section-title {{
      font-family: 'Cormorant Garamond', serif;
      font-size: 24px; font-weight: 700;
      color: var(--forest);
      margin: 36px 0 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border);
      display: flex; align-items: center; gap: 10px;
    }}
    .section-title::before {{
      content: '';
      width: 4px; height: 24px;
      background: linear-gradient(180deg, var(--forest2), var(--gold));
      border-radius: 2px;
      flex-shrink: 0;
    }}

    /* ── TABLE ── */
    .data-table {{
      width: 100%;
      border-collapse: collapse;
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 16px rgba(11,77,50,0.07);
      font-size: 13px;
    }}
    .data-table thead tr {{
      background: var(--forest);
    }}
    .data-table th {{
      color: rgba(255,255,255,0.85);
      padding: 13px 16px;
      text-align: left;
      font-weight: 600;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      border: none;
    }}
    .data-table td {{
      padding: 11px 16px;
      border-bottom: 1px solid var(--ivory2);
      color: var(--text);
    }}
    .data-table tbody tr:last-child td {{ border-bottom: none; }}
    .data-table tbody tr:nth-child(even) {{ background: var(--ivory); }}
    .data-table tbody tr:hover {{ background: rgba(14,107,69,0.04); }}

    /* ── DEPT SUMMARY ── */
    .dept-table {{
      width: 100%;
      border-collapse: collapse;
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 16px rgba(11,77,50,0.07);
      font-size: 13px;
    }}
    .dept-table th {{
      background: var(--forest2);
      color: rgba(255,255,255,0.85);
      padding: 12px 16px;
      text-align: left;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }}
    .dept-table td {{
      padding: 11px 16px;
      border-bottom: 1px solid var(--ivory2);
    }}
    .dept-table tbody tr:nth-child(even) {{ background: var(--ivory); }}
    .dept-table tbody tr:hover {{ background: rgba(14,107,69,0.04); }}

    /* ── HIGHLIGHT BOX ── */
    .highlight-box {{
      background: white;
      border: 1px solid var(--border);
      border-left: 4px solid var(--gold);
      border-radius: 10px;
      padding: 18px 22px;
      margin-bottom: 24px;
      font-size: 13px;
      color: var(--text);
      box-shadow: 0 2px 12px rgba(11,77,50,0.05);
    }}
    .highlight-box strong {{ color: var(--gold); }}

    /* ── FOOTER ── */
    .report-footer {{
      background: var(--forest);
      padding: 22px 60px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 60px;
    }}
    .footer-brand {{
      font-family: 'Cormorant Garamond', serif;
      font-size: 18px; font-weight: 700;
      color: rgba(255,255,255,0.80);
    }}
    .footer-brand em {{ font-style: italic; color: var(--gold2); }}
    .footer-copy {{
      font-size: 12px;
      color: rgba(255,255,255,0.35);
      letter-spacing: 0.5px;
    }}

    @media print {{
      body {{ background: white; }}
      .report-header {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    }}
  </style>
</head>
<body>

  <!-- HEADER -->
  <div class="report-header">
    <div class="header-badge">Rapport Hospitalier</div>
    <div class="report-title"><em>Data</em> Care</div>
    <div class="report-subtitle">Analyse des Données Hospitalières</div>
    <div class="report-date">Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</div>
  </div>

  <!-- BODY -->
  <div class="report-body">

    <!-- HIGHLIGHT -->
    <div class="highlight-box" style="margin-top:32px">
      Département le plus actif : <strong>{top_dept}</strong> &nbsp;·&nbsp;
      Pathologie dominante : <strong>{top_disease}</strong> &nbsp;·&nbsp;
      Période d'analyse : données complètes filtrées
    </div>

    <!-- KPIs -->
    <div class="kpi-grid">
      <div class="kpi-card k1">
        <div class="kpi-val">{len(filtered_df):,}</div>
        <div class="kpi-lbl">👥 Patients analysés</div>
      </div>
      <div class="kpi-card k2">
        <div class="kpi-val">{filtered_df['DureeSejour'].mean():.1f} j</div>
        <div class="kpi-lbl">📅 Durée moyenne</div>
      </div>
      <div class="kpi-card k3">
        <div class="kpi-val">{filtered_df['Cout'].mean():,.0f} €</div>
        <div class="kpi-lbl">💶 Coût moyen</div>
      </div>
      <div class="kpi-card k4">
        <div class="kpi-val">{filtered_df['Cout'].sum():,.0f} €</div>
        <div class="kpi-lbl">💰 Coût total</div>
      </div>
    </div>

    <!-- RESUME PAR DEPT -->
    <div class="section-title">Résumé par Département</div>
    <table class="dept-table">
      <thead><tr>
        <th>Département</th>
        <th style="text-align:center">Patients</th>
        <th style="text-align:center">Coût Moyen</th>
        <th style="text-align:center">Durée Moy.</th>
      </tr></thead>
      <tbody>{dept_rows}</tbody>
    </table>

    <!-- DONNEES COMPLETES -->
    <div class="section-title">Données Complètes des Patients</div>
    {filtered_df.to_html(index=False, classes='data-table', border=0)}

  </div><!-- /report-body -->

  <!-- FOOTER -->
  <div class="report-footer">
    <div class="footer-brand"><em>Data</em> Care</div>
    <div class="footer-copy">© 2025 DATA CARE — Optimizing Patient Care with Data Intelligence</div>
  </div>

</body>
</html>"""
        
        return dict(content=stats_html, 
                   filename=f"rapport_hospital_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    
    # ============================================================================
    # CALLBACK 6 : TÉLÉCHARGER PDF (avec reportlab)
    # ============================================================================
    @app.callback(
        Output("download-pdf", "data"),
        Input("btn-download-pdf", "n_clicks"),
        [State('dept-filter', 'value'),
         State('disease-filter', 'value'),
         State('treatment-filter', 'value'),
         State('age-filter', 'value')],
        prevent_initial_call=True
    )
    def download_pdf(n_clicks, dept_values, disease_values, treatment_values, age_range):
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            
            # Filtrer les données
            filtered_df = df.copy()
            
            if dept_values:
                filtered_df = filtered_df[filtered_df['Departement'].isin(dept_values)]
            
            if disease_values:
                filtered_df = filtered_df[filtered_df['Maladie'].isin(disease_values)]
            
            if treatment_values:
                filtered_df = filtered_df[filtered_df['Traitement'].isin(treatment_values)]
            
            if age_range:
                filtered_df = filtered_df[(filtered_df['Age'] >= age_range[0]) & 
                                         (filtered_df['Age'] <= age_range[1])]
            
            # Créer un buffer
            buffer = io.BytesIO()
            
            # Créer le PDF
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []
            
            # Styles — palette Clinique Naturelle
            styles = getSampleStyleSheet()
            
            FOREST  = colors.HexColor('#0B4D32')
            FOREST2 = colors.HexColor('#0E6B45')
            GOLD    = colors.HexColor('#B8860B')
            GOLD2   = colors.HexColor('#E8A320')
            CLAY    = colors.HexColor('#8B4513')
            SAGE    = colors.HexColor('#4A7C59')
            IVORY   = colors.HexColor('#F7F3EE')
            IVORY2  = colors.HexColor('#EDE7DC')
            TEXT    = colors.HexColor('#1C2820')
            TEXTM   = colors.HexColor('#7A9080')

            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=28,
                textColor=FOREST,
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            subtitle_style = ParagraphStyle(
                'Subtitle',
                parent=styles['Normal'],
                fontSize=11,
                textColor=TEXTM,
                spaceAfter=24,
                alignment=TA_CENTER,
            )
            section_style = ParagraphStyle(
                'Section',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=FOREST2,
                spaceBefore=18,
                spaceAfter=10,
                fontName='Helvetica-Bold'
            )
            
            # ── Titre ──
            elements.append(Paragraph("DATA CARE", title_style))
            elements.append(Paragraph(
                f"Rapport Hospitalier · Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}",
                subtitle_style
            ))
            elements.append(Spacer(1, 0.2*inch))
            
            # ── Ligne décorative ──
            from reportlab.platypus import HRFlowable
            elements.append(HRFlowable(width="100%", thickness=2, color=FOREST2, spaceAfter=16))
            
            # ── KPIs ──
            elements.append(Paragraph("Indicateurs Clés", section_style))
            stats_data = [
                ['Indicateur', 'Valeur'],
                ['👥  Patients analysés',  f"{len(filtered_df):,}"],
                ['📅  Durée moyenne',       f"{filtered_df['DureeSejour'].mean():.1f} jours"],
                ['💶  Coût moyen',          f"{filtered_df['Cout'].mean():,.0f} €"],
                ['💰  Coût total',          f"{filtered_df['Cout'].sum():,.0f} €"],
            ]
            stats_table = Table(stats_data, colWidths=[3.5*inch, 2.5*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND',   (0,0), (-1,0),  FOREST),
                ('TEXTCOLOR',    (0,0), (-1,0),  colors.white),
                ('FONTNAME',     (0,0), (-1,0),  'Helvetica-Bold'),
                ('FONTSIZE',     (0,0), (-1,0),  10),
                ('ALIGN',        (0,0), (-1,-1), 'LEFT'),
                ('PADDING',      (0,0), (-1,-1), 10),
                ('BACKGROUND',   (0,1), (-1,1),  IVORY),
                ('BACKGROUND',   (0,2), (-1,2),  colors.white),
                ('BACKGROUND',   (0,3), (-1,3),  IVORY),
                ('BACKGROUND',   (0,4), (-1,4),  colors.white),
                ('TEXTCOLOR',    (1,1), (1,1),   FOREST2),
                ('TEXTCOLOR',    (1,2), (1,2),   GOLD),
                ('TEXTCOLOR',    (1,3), (1,3),   SAGE),
                ('TEXTCOLOR',    (1,4), (1,4),   CLAY),
                ('FONTNAME',     (1,1), (1,-1),  'Helvetica-Bold'),
                ('FONTSIZE',     (1,1), (1,-1),  12),
                ('GRID',         (0,0), (-1,-1), 0.5, IVORY2),
                ('ROUNDEDCORNERS', [4]),
            ]))
            elements.append(stats_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # ── Données patients ──
            elements.append(HRFlowable(width="100%", thickness=1, color=IVORY2, spaceAfter=10))
            elements.append(Paragraph("Données Patients (50 premières lignes)", section_style))
            elements.append(Spacer(1, 0.1*inch))
            
            df_pdf = filtered_df[['PatientID', 'Age', 'Sexe', 'Departement', 'Maladie',
                                  'DureeSejour', 'Cout']].head(50)
            data = [df_pdf.columns.tolist()] + df_pdf.values.tolist()
            
            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND',  (0,0),  (-1,0),  FOREST),
                ('TEXTCOLOR',   (0,0),  (-1,0),  colors.white),
                ('FONTNAME',    (0,0),  (-1,0),  'Helvetica-Bold'),
                ('FONTSIZE',    (0,0),  (-1,0),  8),
                ('ALIGN',       (0,0),  (-1,-1), 'CENTER'),
                ('PADDING',     (0,0),  (-1,-1), 6),
                ('FONTSIZE',    (0,1),  (-1,-1), 7),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, IVORY]),
                ('GRID',        (0,0),  (-1,-1), 0.4, IVORY2),
                ('TEXTCOLOR',   (0,1),  (-1,-1), TEXT),
            ]))
            elements.append(table)
            
            # ── Footer ──
            elements.append(Spacer(1, 0.4*inch))
            elements.append(HRFlowable(width="100%", thickness=1, color=FOREST2, spaceAfter=10))
            elements.append(Paragraph(
                "© 2025 DATA CARE — Optimizing Patient Care with Data Intelligence",
                ParagraphStyle('Footer', parent=styles['Normal'],
                               fontSize=9, textColor=TEXTM, alignment=TA_CENTER)
            ))
            
            # Construire le PDF
            doc.build(elements)
            
            buffer.seek(0)
            
            return dcc.send_bytes(buffer.getvalue(), 
                                 f"rapport_hospital_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        
        except ImportError:
            # Si reportlab n'est pas installé, retourner un message
            message = """
            ⚠️ ERREUR : reportlab n'est pas installé
            
            Pour générer des PDF, installez :
            pip install reportlab
            
            Puis relancez l'application.
            """
            
            return dict(content=message, 
                       filename=f"erreur_pdf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
