# ============================================================
# 🚀 AI-ASSISTED CODE NOTICE
# This file was developed with assistance from OpenAI's ChatGPT (GPT-5)
# as part of the NASA Space Apps 2025 project:
# "TerraWatt — Will It Rain on My Parade?"
# ============================================================

"""
test_optimal_zones.py
---------------------
Test script to verify optimal zones calculation works correctly.
"""

import os
import sys
import pandas as pd

# Add src to path
sys.path.append('src')

def test_data_loading():
    """Test if data files exist and can be loaded."""
    print("🔍 Testing data file availability...")
    
    # Check ERA5 data
    era5_csv = "data/era5/era5_ireland_mean_wind_1994_2024.csv"
    if os.path.exists(era5_csv):
        print(f"✅ ERA5 wind data found: {era5_csv}")
        df = pd.read_csv(era5_csv)
        print(f"   - Shape: {df.shape}")
        print(f"   - Columns: {list(df.columns)}")
        print(f"   - Wind speed range: {df['wind_speed_10m'].min():.2f} - {df['wind_speed_10m'].max():.2f} m/s")
    else:
        print(f"❌ ERA5 wind data not found: {era5_csv}")
    
    # Check grid data
    subs_path = "data/osm/substations_110kV_clean.geojson"
    lines_path = "data/osm/lines_110kV_clean.geojson"
    
    if os.path.exists(subs_path):
        print(f"✅ Substations data found: {subs_path}")
    else:
        print(f"❌ Substations data not found: {subs_path}")
    
    if os.path.exists(lines_path):
        print(f"✅ Transmission lines data found: {lines_path}")
    else:
        print(f"❌ Transmission lines data not found: {lines_path}")
    
    # Check wind farms data
    wind_path = "data/wind_farms/Wind Farms June 2022_ESPG3857.shp"
    if os.path.exists(wind_path):
        print(f"✅ Wind farms data found: {wind_path}")
    else:
        print(f"❌ Wind farms data not found: {wind_path}")

def test_optimal_zones_import():
    """Test if optimal zones module can be imported."""
    print("\n🔍 Testing optimal zones module import...")
    
    try:
        from src.analysis.optimal_zones import calculate_optimal_zones, load_era5_wind_data
        print("✅ Optimal zones module imported successfully")
        
        # Test data loading
        wind_data = load_era5_wind_data()
        if wind_data is not None:
            print(f"✅ Wind data loaded: {len(wind_data)} points")
        else:
            print("❌ Wind data loading failed")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_visualization_import():
    """Test if visualization module can be imported."""
    print("\n🔍 Testing visualization module import...")
    
    try:
        from src.visualization.optimal_zones_viz import create_optimal_zones_map
        print("✅ Visualization module imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_optimal_zones_calculation():
    """Test optimal zones calculation and create a simple map."""
    print("\n🔍 Testing optimal zones calculation...")
    
    try:
        from src.analysis.optimal_zones import generate_optimal_zones
        print("✅ Starting optimal zones calculation...")
        
        # Generate optimal zones
        zones_gdf, cluster_stats = generate_optimal_zones()
        print(f"✅ Generated {len(zones_gdf)} optimal zones")
        print(f"✅ Found {len(cluster_stats)} development clusters")
        
        # Show zone categories
        category_counts = zones_gdf['zone_category'].value_counts()
        print(f"✅ Zone categories: {category_counts.to_dict()}")
        
        # Show top zones
        top_zones = zones_gdf.nlargest(5, 'composite_score')
        print("\n🏆 Top 5 Optimal Zones:")
        for _, zone in top_zones.iterrows():
            print(f"   {zone['latitude']:.3f}, {zone['longitude']:.3f} - {zone['zone_category']} "
                  f"(Wind: {zone['wind_speed_mps']:.1f} m/s, Score: {zone['composite_score']:.2f})")
        
        return zones_gdf, cluster_stats
        
    except Exception as e:
        print(f"❌ Optimal zones calculation failed: {e}")
        return None, None

def create_simple_map(zones_gdf, cluster_stats):
    """Create a simple map visualization using folium."""
    print("\n🗺️ Creating map visualization...")
    
    try:
        import folium
        from streamlit_folium import st_folium
        
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
        print(f"✅ Map saved to: {map_path}")
        
        return m, map_path
        
    except ImportError as e:
        print(f"❌ Folium not available: {e}")
        return None, None
    except Exception as e:
        print(f"❌ Map creation failed: {e}")
        return None, None

def main():
    """Run all tests and create map."""
    print("🚀 Testing Optimal Zones Implementation")
    print("=" * 50)
    
    test_data_loading()
    test_optimal_zones_import()
    test_visualization_import()
    
    # Test optimal zones calculation
    zones_gdf, cluster_stats = test_optimal_zones_calculation()
    
    if zones_gdf is not None:
        # Create map visualization
        map_obj, map_path = create_simple_map(zones_gdf, cluster_stats)
        
        if map_path:
            print(f"\n🌐 Open the map in your browser: file://{os.path.abspath(map_path)}")
            print("   Or run: streamlit run app.py and select 'Optimal Zones Analysis'")
    
    print("\n✅ Testing complete!")

if __name__ == "__main__":
    main()
