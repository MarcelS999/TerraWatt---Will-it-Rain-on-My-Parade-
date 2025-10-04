🛠️ Installation Guide
1. Clone the repository
git clone https://github.com/MarcelS999/TerraWatt---Will-it-Rain-on-My-Parade.git
cd TerraWatt---Will-it-Rain-on-My-Parade

2. Create and activate the environment
conda env create -f environment.yml
conda activate parade


(If using pip, you can instead run pip install -r requirements.txt.)

3. Launch the app
streamlit run app.py

🗺️ How to Use

Open the map in your browser (Streamlit will show the local URL).

Explore Ireland’s wind variability layer.

Click any point to generate a detailed site summary — including mean wind speed, CF, and nearest grid connection.

📂 Repository Structure
├── app.py                         # Main Streamlit map app
├── data/
│   ├── era5/                      # ERA5 climatology & CF datasets
│   ├── osm/                       # Transmission grid layers
│   └── wind_farms/                # Wind farm shapefile
├── src/
│   ├── analysis/                  # Site summary & CF computations
│   ├── processing/                # Wind extrapolation utilities
│   └── visualization/             # Map rendering tools
├── environment.yml                # Conda environment file
└── README.md                      # This file
