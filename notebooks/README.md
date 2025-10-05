# Test Scripts for Wind Farm Data Analysis

This folder contains test scripts for examining and testing wind farm data extraction and visualization features.

## Scripts Overview

### 1. `examine_wind_data.py`
**Purpose**: Basic examination of wind farm data structure without external dependencies.

**Usage**:
```bash
cd notebooks
python examine_wind_data.py
```

**What it does**:
- Checks if wind farm data files exist
- Lists available data files
- Provides basic information about data structure

### 2. `test_wind_farm_data.py`
**Purpose**: Comprehensive testing of wind farm data loading and field extraction.

**Usage**:
```bash
cd notebooks
python test_wind_farm_data.py
```

**Requirements**:
- geopandas
- pandas

**What it does**:
- Loads wind farm shapefile data
- Tests name and capacity extraction functions
- Shows sample data and extracted information
- Validates popup HTML generation

### 3. `test_wind_farm_tooltips.py`
**Purpose**: Creates a test map with wind farm tooltips for visualization testing.

**Usage**:
```bash
cd notebooks
python test_wind_farm_tooltips.py
```

**Requirements**:
- folium
- geopandas
- streamlit
- pandas

**What it does**:
- Creates an interactive Folium map
- Adds wind farm markers with enhanced tooltips
- Tests the complete tooltip system
- Saves test map as HTML file

### 4. `test_era5_solar_api.py`
**Purpose**: Tests the enhanced ERA5 API with solar irradiance data.

**Usage**:
```bash
cd notebooks
python test_era5_solar_api.py
```

**Requirements**:
- planetary-computer
- pystac-client
- xarray
- pandas

**What it does**:
- Tests ERA5 data fetching with solar variables
- Validates wind and solar data extraction
- Shows summary statistics and data quality
- Demonstrates API parameter combinations

### 5. `example_solar_wind_analysis.py`
**Purpose**: Comprehensive example of solar and wind resource analysis.

**Usage**:
```bash
cd notebooks
python example_solar_wind_analysis.py
```

**Requirements**:
- planetary-computer
- pystac-client
- xarray
- pandas
- folium (for visualizations)

**What it does**:
- Demonstrates seasonal solar analysis
- Shows wind-solar correlation analysis
- Performs renewable energy potential assessment
- Creates example visualizations

### 6. `analyze_era5_data.py`
**Purpose**: Analyzes existing ERA5 data structure and content.

**Usage**:
```bash
cd notebooks
python analyze_era5_data.py
```

**Requirements**:
- pandas

**What it does**:
- Examines ERA5 data files and structure
- Shows file sizes and data coverage
- Displays wind speed statistics and patterns
- Provides data quality assessment

## Data Requirements

All scripts expect the wind farm data to be located at:
```
../data/wind_farms/Wind Farms June 2022_ESPG3857.shp
```

## Installation

To run the test scripts, install the required dependencies:

### Basic Dependencies
```bash
pip install geopandas folium streamlit pandas
```

### ERA5 Solar API Dependencies
```bash
pip install planetary-computer pystac-client xarray
```

### Optional Dependencies (for advanced features)
```bash
pip install rioxarray  # For GeoTIFF processing
pip install netCDF4    # For NetCDF file handling
```

## Output Files

- `test_wind_farm_map.html`: Interactive test map with wind farm tooltips (created by test_wind_farm_tooltips.py)

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'geopandas'**
   - Solution: Install geopandas: `pip install geopandas`

2. **FileNotFoundError: Wind farm data not found**
   - Solution: Ensure the data files are in the correct location: `../data/wind_farms/`

3. **UnicodeEncodeError**
   - Solution: The scripts have been updated to avoid Unicode issues in Windows terminals

### Running from Different Directories

If running from the project root instead of the notebooks folder:

```bash
# From project root
python notebooks/test_wind_farm_data.py
python notebooks/test_wind_farm_tooltips.py
python notebooks/examine_wind_data.py
```

## Features Tested

### Wind Farm Analysis
- Wind farm name extraction from various field names
- Wind farm capacity extraction with unit handling
- HTML popup generation with rich formatting
- Interactive map creation with tooltips
- Data validation and error handling
- Path resolution for different working directories

### ERA5 Solar & Wind API
- Enhanced ERA5 data fetching with solar irradiance
- Wind speed calculations at 10m and 100m heights
- Solar irradiance and capacity factor calculations
- Seasonal and temporal analysis capabilities
- Wind-solar correlation analysis
- Renewable energy potential assessment
- Interactive map creation with solar heatmaps
- Multiple output formats (CSV, NetCDF, GeoTIFF)

### Data Processing
- Spatial resampling and interpolation
- Coordinate system conversions
- Data quality validation and statistics
- Batch processing for multiple time periods
- Integration with existing wind farm data
