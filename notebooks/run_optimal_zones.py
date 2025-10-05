# ============================================================
# 🚀 AI-ASSISTED CODE NOTICE
# This file was developed with assistance from OpenAI's ChatGPT (GPT-5)
# as part of the NASA Space Apps 2025 project:
# "TerraWatt — Will It Rain on My Parade?"
# ============================================================

"""
run_optimal_zones.py
--------------------
Simple script to run optimal zones calculation and open a map.
"""

import os
import sys
import webbrowser
from pathlib import Path

# Add src to path
sys.path.append('src')

def main():
    """Run optimal zones calculation and create map."""
    print("Running Optimal Zones Calculation")
    print("=" * 50)
    
    try:
        # Import and run optimal zones calculation
        from src.analysis.optimal_zones import generate_optimal_zones
        print("Starting optimal zones calculation...")
        
        # Generate optimal zones
        zones_gdf, cluster_stats = generate_optimal_zones()
        print(f"Generated {len(zones_gdf)} optimal zones")
        print(f"Found {len(cluster_stats)} development clusters")
        
        # Show zone categories
        category_counts = zones_gdf['zone_category'].value_counts()
        print(f"Zone categories: {category_counts.to_dict()}")
        
        # Show top zones
        top_zones = zones_gdf.nlargest(5, 'composite_score')
        print("\nTop 5 Optimal Zones:")
        for _, zone in top_zones.iterrows():
            print(f"   {zone['latitude']:.3f}, {zone['longitude']:.3f} - {zone['zone_category']} "
                  f"(Wind: {zone['wind_speed_mps']:.1f} m/s, Score: {zone['composite_score']:.2f})")
        
        # Create map visualization
        print("\nCreating map visualization...")
        import folium
        
        # Create base map
        m = folium.Map(location=[53.5, -8], zoom_start=7, tiles="CartoDB positron")
        
        # Add optimal zones
        for _, row in zones_gdf.iterrows():
            color = {
                'Excellent': 'green',
                'Good': 'lightgreen', 
                'Moderate': 'yellow',
                'Marginal': 'orange'
            }.get(row['zone_category'], 'gray')
            
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=8,
                color=color,
                fill=True,
                fillOpacity=0.7,
                popup=folium.Popup(
                    f"""
                    <b>Optimal Wind Zone</b><br>
                    Category: {row['zone_category']}<br>
                    Wind Speed: {row['wind_speed_mps']:.1f} m/s<br>
                    Grid Distance: {row['grid_distance_km']:.1f} km<br>
                    Grid Cost: €{row['grid_cost_eur']:,.0f}<br>
                    Score: {row['composite_score']:.2f}
                    """,
                    max_width=200
                )
            ).add_to(m)
        
        # Add cluster centers
        if cluster_stats:
            for cluster in cluster_stats:
                folium.Marker(
                    location=[cluster['centroid_lat'], cluster['centroid_lon']],
                    icon=folium.Icon(color='red', icon='star'),
                    popup=folium.Popup(
                        f"""
                        <b>Development Cluster {cluster['cluster_id']}</b><br>
                        Zones: {cluster['count']}<br>
                        Avg Wind: {cluster['avg_wind_speed']:.1f} m/s<br>
                        Avg Score: {cluster['avg_score']:.2f}
                        """,
                        max_width=200
                    )
                ).add_to(m)
        
        # Add legend
        legend_html = """
        <div style="position: fixed; bottom: 50px; left: 50px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Optimal Zones Legend</b></p>
        <p><i class="fa fa-circle" style="color:green"></i> Excellent</p>
        <p><i class="fa fa-circle" style="color:lightgreen"></i> Good</p>
        <p><i class="fa fa-circle" style="color:yellow"></i> Moderate</p>
        <p><i class="fa fa-circle" style="color:orange"></i> Marginal</p>
        <p><i class="fa fa-star" style="color:red"></i> Cluster Centers</p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        map_path = "optimal_zones_map.html"
        m.save(map_path)
        print(f"Map saved to: {map_path}")
        
        # Get absolute path and open in browser
        abs_path = os.path.abspath(map_path)
        file_url = f"file://{abs_path}"
        print(f"Opening map in browser: {file_url}")
        
        # Open in default browser
        webbrowser.open(file_url)
        
        print("\nOptimal zones calculation complete!")
        print(f"Total zones: {len(zones_gdf)}")
        print(f"Development clusters: {len(cluster_stats)}")
        print(f"Map opened in browser")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
