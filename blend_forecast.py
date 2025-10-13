import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import xarray as xr
from scipy import stats
import pygrib

import os
import re
import subprocess
from datetime import datetime
import seaborn as sns
sns.set_theme()

import logging
import argparse
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():

    desc = """run postprocessing."""
    p = argparse.ArgumentParser(description=desc)
    p.add_argument("-o", "--option", required=True, help='basic_data_info' )
    p.add_argument("-c", "--city", required=False, help='city name for location-specific plots' )
    args = p.parse_args()
    
    option= args.option
    city=args.city 


    if option=='basic_data_info':
        basic_data_info()

    elif option=='download': 
        download_forecast()
    
    elif option=='process_forecast':
        process_forecast(city)
    
    elif option=='get_forecast':
        forecast2(city)
    
    else:
        logger.error("Unrecognized command line argument. \n  Commands available -o download, -o get_forecast")


def process_forecast(city):
    path_dir = "data/alaro/"
    coordinates = get_city_coordinates(city)
    u_files, v_files, temp_files, precip_files, humidity_files, path_folder, initial_file = find_latest_alaro_uv_files() 
    print("Path file:", initial_file)
    idx_lat, idx_lon, initial_time = basic_data_info(initial_file, coordinates, city) 

    time_txt = pd.to_datetime(initial_time.values).to_pydatetime()
    ref_time = time_txt.strftime("%Y-%m-%d_%H") 

    time_txt = pd.to_datetime(initial_time.values).to_pydatetime()
    time_txt = datetime.strptime(str(time_txt)[:13], "%Y-%m-%d %H")

    color_label = ["tab:red", "tab:orange","tab:green", "tab:blue"]
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(f"Weather Forecast for {city.capitalize()} - {str(ref_time)}", fontsize=16, fontweight='bold')

    for tt in range(4):
    
        df_wind = wind_speed_grib(u_files[tt], v_files[tt], path_folder, coordinates, city)
        df_temp_precip = temperature_grib(temp_files[tt], precip_files[tt], humidity_files[tt], path_folder, coordinates, city)
        axs[0, 0].set_title("Temperature")
        axs[0, 0].plot(df_temp_precip['time'], df_temp_precip['temperature']-273.15, color=color_label[tt])
        axs[0, 0].set_ylim(0, 30)
        axs[1, 0].set_title("Precipitation")
        axs[1, 0].plot(df_temp_precip['time'], df_temp_precip['hourly_rainfall']*1000, color=color_label[tt])
        axs[1, 0].set_ylim(-0.1, 6)
        axs[0, 1].set_title("Wind speed")
        axs[0, 1].plot(df_wind['time'], df_wind['wind_speed'], color=color_label[tt])
        axs[0, 1].set_ylim(0, 12)
        axs[1, 1].set_title("Wind direction")
        axs[1, 1].plot(df_wind['time'], df_wind['wind_direction'], color=color_label[tt])
        axs[1, 1].set_ylim(0, 360)
        axs[1, 1].set_yticks(np.arange(0, 361, 60))

    for ss in range(2):
            axs[1, ss].set_xlabel("Time")
            axs[1, ss].grid(True)
            axs[1, ss].tick_params(axis='x', rotation=30)

    for ff in range(2):
        axs[0, ff].set_xticklabels([])

    axs[0, 0].set_ylabel("Temperature [°C]")
    axs[0, 1].set_ylabel("Wind speed [m/s]")
    axs[1, 0].set_ylabel("Hourly rainfall [mm]")

    filename = 'weather_forecast_'+ city+'_'+ref_time+'.png'
    plt.savefig(filename, dpi=400)
    print(f"Weather Forecast for {city.capitalize()}")
    print('Saved as: ', 'weather_forecast_'+ city+'_'+ref_time+'.png')
    os.system(f"code {filename}")

    # finaly additional statistical analysis  
def wind_speed_grib(u_files, v_files, path_folder, coordinates, city):
    #u_files = ['alaro40l_2025062418_10U.grb']
    #v_files = ['alaro40l_2025062418_10V.grb']

    file_0 = path_folder + u_files  # Use the first file to get basic data info 
    idx_lat, idx_lon, initial_time = basic_data_info(file_0, coordinates, city)

    time_txt = pd.to_datetime(initial_time.values).to_pydatetime()
    ref_time = time_txt.strftime("%Y-%m-%d_%H") 

    grib_u = xr.open_dataset(path_folder + u_files, engine='cfgrib', decode_timedelta=False)
    grib_v = xr.open_dataset(path_folder + v_files, engine='cfgrib', decode_timedelta=False)

    u10 = grib_u['unknown']
    v10 = grib_v['unknown']
    
    wind_speed = np.sqrt(np.power(u10[:, idx_lat,idx_lon], 2) + np.power(v10[:, idx_lat,idx_lon], 2))
    wind_dir = (np.degrees(np.arctan2(u10[:, idx_lat,idx_lon], v10[:, idx_lat,idx_lon])) + 180 + 360) % 360

    initial_time = pd.to_datetime(initial_time.values).to_pydatetime()
    initial_time = datetime.strptime(str(initial_time)[:16], "%Y-%m-%d %H:%M")
    n_steps = len(wind_speed)  
    times = [initial_time + timedelta(hours=i) for i in range(n_steps)]
    df = pd.DataFrame({
    'time': times,
    'wind_speed': wind_speed,
    'wind_direction': wind_dir
        })

    df.to_csv(path_folder+ "wind_data_"+str(ref_time)+"_"+city+".csv", index=False)
    return df

def basic_data_info(file, coordinates, city):
    #path = '/home/mamanicr/projects/atmoflow_f1/data/alaro/alaro_25_06/'
    #file_name = 'alaro40l_2025062406_10U.grb'
    grib = xr.open_dataset(file, engine='cfgrib', decode_timedelta=False)
    #print(grib.data_vars)
    initial_time = grib['time']
    latitude = grib['latitude']
    longitude = grib['longitude']
    coordinates[0]
    # Spa Frnacorchamps
    #target_lat = 50.44335
    #target_lon = 5.9682
    target_lat = coordinates[0]
    target_lon = coordinates[1]
    # VITO TAP
    #target_lat = 51.2185
    #target_lon = 5.0794

    idx_lat = (np.abs(latitude-target_lat)).argmin()
    idx_lon = (np.abs(longitude-target_lon)).argmin()
    #print(f"Weather Forecast for {city.capitalize()}")
    #print('Target point : ', target_lat,  target_lon)
    #print('Nearest point: ', f"{latitude[idx_lat].values:.4f}", f"{longitude[idx_lon].values:.4f}")
    return idx_lat, idx_lon, initial_time


def download_forecast():
    today = datetime.now()
    folder_to_save = "data/alaro/"
    folder_name = folder_to_save+f"alaro_{today.year}_{today.month:02}_{today.day:02}"

    os.makedirs(folder_name, exist_ok=True)

    ftp_url = "ftp://opendata24-me.oma.be/forecasts/alaro_40l/"
    wget_cmd = [
        "wget",
        "-r",  # recursive
        "-nH",  # don't create hostname dir
        "--cut-dirs=3",  # trim path prefix
       # "--accept", "*10U*,*10V*",  # filter files 
        "--accept", "*10U*,*10V*,*2T*,*TotPrecip*, *RH2M*",  # filter files
        "-P", folder_name,  # download path
        ftp_url
    ]

    print("Running wget to download filtered ALARO GRIB files...")
    subprocess.run(wget_cmd, check=True)
    print(f"Download complete. Files saved in: {folder_name}")


def plot_wind_speed():

    u_files, v_files, temp_files, precip_files, path_folder = find_latest_alaro_uv_files()
    print(path_folder)

    for u_file, v_file in zip(u_files, v_files):
        df = wind_speed_grib(u_file, v_file, path_folder)
        wind_s = df['wind_speed']
        plt.figure(1, figsize=(10, 5))
        plt.plot(df['time'], wind_s, label=str(u_file))

    plt.title('Wind speed in Mol')
    plt.xlabel('Hour')
    plt.ylabel('Wind speed (m/s)')
    plt.legend()
    plt.savefig('wind_speed_'+str(u_file)+'.png', dpi=360)

    for u_file, v_file in zip(u_files, v_files):
        df = wind_speed_grib(u_file, v_file, path_folder)
        wind_s = df['wind_direction']
        plt.figure(2, figsize=(10, 5))
        plt.plot(df['time'], wind_s, label=str(u_file))

    plt.title('Wind direction in Mol')
    plt.xlabel('Hour')
    plt.ylabel('Wind direction (-)')
    plt.legend()
    plt.savefig('wind_direction_'+str(u_file)+'.png', dpi=360)

def temperature_grib(temp_files, precip_files, humidity_files, path_folder,coordinates, city):

    file_0 = path_folder + temp_files  # Use the first file to get basic data info 
    idx_lat, idx_lon, initial_time = basic_data_info(file_0, coordinates, city)

    time_txt = pd.to_datetime(initial_time.values).to_pydatetime()
    ref_time = time_txt.strftime("%Y-%m-%d_%H") 

    grib_temp = xr.open_dataset(path_folder + temp_files, engine='cfgrib', decode_timedelta=False)
    grib_precip = xr.open_dataset(path_folder + precip_files, engine='cfgrib', decode_timedelta=False)
    grib_humidity = xr.open_dataset(path_folder + humidity_files, engine='cfgrib', decode_timedelta=False)
    temp = grib_temp['unknown']
    precip = grib_precip['v10n']
    humid = grib_humidity['unknown']  # Assuming humidity is also in the precip file, adjust if needed

    temperature = temp[:, idx_lat,idx_lon]
    precipitation = precip[:, idx_lat,idx_lon]
    humidity = humid[:, idx_lat,idx_lon]  # Assuming humidity is also in the precip file, adjust if needed
    hourly_rainfall = np.roll(precipitation, -1, axis=0) - precipitation
    hourly_rainfall[-1] = np.nan  # Set last timestep to NaN (no "next" value)
    initial_time = pd.to_datetime(initial_time.values).to_pydatetime()
    initial_time = datetime.strptime(str(initial_time)[:16], "%Y-%m-%d %H:%M")
    n_steps = len(temperature)  
    times = [initial_time + timedelta(hours=i) for i in range(n_steps)]
    #print("Computing temperature and precipitation")
    df_temp_precip = pd.DataFrame({
    'time': times,
    'temperature': temperature,
    'precipitation': precipitation,
    'hourly_rainfall': hourly_rainfall,
    'humidity': humidity
        })

    df_temp_precip.to_csv(path_folder+ "temp_humdity_precip_data_"+str(ref_time)+"_"+city+".csv", index=False)
    return df_temp_precip


def plot_temperature():
    u_files, v_files, temp_files, precip_files, path_folder = find_latest_alaro_uv_files()
    print(path_folder)

    for temp_file, precip_file in zip(temp_files, precip_files):
        df_temp_precip = temperature_grib(temp_file, precip_file, path_folder)
        plt.figure(3, figsize=(10, 5))
        plt.plot(df_temp_precip['time'], df_temp_precip['temperature']-273.15, label=str(temp_file))

    plt.title('Temperature forecast in MOL')
    plt.xlabel('Date')
    plt.ylabel('Temperature (Celsius)')
    plt.legend()
    plt.savefig('temperature_C_'+str(temp_file)+'.png', dpi=360)

    for temp_file, precip_file in zip(temp_files, precip_files):
        df_temp_precip = temperature_grib(temp_file, precip_file, path_folder)
        plt.figure(4, figsize=(10, 5))
        plt.plot(df_temp_precip['time'], df_temp_precip['precipitation'], label=str(precip_file))

    plt.title('Precipitation forecast in MOL')
    plt.xlabel('Date')
    plt.ylabel('precipitation (mm)')
    plt.legend()
    plt.savefig('precipitation_'+str(precip_file)+'.png')


def find_latest_alaro_uv_files():
    base_dir = "data/alaro/"

    # get a list of folders matching the pattern
    folder_pattern = re.compile(r"alaro_(\d{4})_(\d{2})_(\d{2})")
    dated_folders = []

    for folder in os.listdir(base_dir):
        match = folder_pattern.match(folder)
        if match:
            y, m, d = match.groups()
            folder_date = int(y + m + d)  # e.g. 20250627
            dated_folders.append((folder_date, folder))

    if not dated_folders:
        raise ValueError("No folders found matching pattern alaro_YYYY_MM_DD")

    # sort by date descending to get the latest
    dated_folders.sort(reverse=True)
    latest_folder = dated_folders[0][1]
    latest_folder_path = os.path.join(base_dir, latest_folder)

    # list all files in the latest folder
    files = os.listdir(latest_folder_path)
    #print(files)
    # filter 10U and 10V
    u_files = [f for f in files if "10U" in f and f.endswith(".grb")]
    v_files = [f for f in files if "10V" in f and f.endswith(".grb")]
    temp_files = [f for f in files if "2T" in f and f.endswith(".grb")]
    precip_files = [f for f in files if "TotPrecip" in f and f.endswith(".grb")]
    humidity_files = [f for f in files if "RH2M" in f and f.endswith(".grb")]
    print(f"Latest folder: {latest_folder_path}")
    #print(u_files)
    #print(temp_files)
    path = latest_folder_path + '/'
    initial_file = path + u_files[0]  # Use the first file to get basic data info
    return u_files, v_files, temp_files, precip_files, humidity_files, path, initial_file
######################################################################################

def forecast2(city):
    """
    Builds probabilistic bands across 4 forecasts spaced 6h apart.
    - The most recent (last) forecast is treated as most probable.
    - Plots weighted median as the central line and shaded IQR (25–75%) + 10–90% ranges.
    - Keeps other helper functions unchanged (wind_speed_grib, temperature_grib, etc.).
    """
    # ---------- helpers ----------
    def weighted_quantile(values, quantiles, sample_weight=None):
        """
        Compute weighted quantiles of `values` for quantiles in [0,1].
        values: array-like (n,)
        quantiles: array-like
        sample_weight: array-like (n,)
        """
        values = np.asarray(values)
        quantiles = np.asarray(quantiles)
        if sample_weight is None:
            sample_weight = np.ones_like(values, dtype=float)
        else:
            sample_weight = np.asarray(sample_weight, dtype=float)

        sorter = np.argsort(values)
        values, sample_weight = values[sorter], sample_weight[sorter]
        weighted_cdf = np.cumsum(sample_weight) - 0.5 * sample_weight
        weighted_cdf /= np.sum(sample_weight)
        return np.interp(quantiles, weighted_cdf, values)

    def align_angles_to_reference(deg_series, ref0_deg):
        """
        Align a direction series (in degrees) to a reference angle to avoid wrap issues.
        Returns radians, unwrapped & aligned.
        """
        r = np.deg2rad(np.asarray(deg_series, dtype=float))
        r = np.unwrap(r)  # time-wise unwrap for smoothness
        ref0 = np.deg2rad(ref0_deg)
        # shift by multiples of 2π to be closest to reference at t0
        shift = np.round((ref0 - r[0]) / (2*np.pi)) * (2*np.pi)
        return r + shift

    def weighted_direction_quantiles(dir_members_deg, weights, qs):
        """
        dir_members_deg: list of 1D arrays (per member) in degrees (0..360)
        weights: (M,) weights per member (sum > 0)
        qs: list of quantiles in [0,1]
        Returns arrays (per time) of weighted quantiles in degrees (0..360).
        Strategy: align each member to the last member's first angle, unwrap, then
        compute weighted quantiles in radians and wrap back to [0,360).
        """
        M = len(dir_members_deg)
        T = len(dir_members_deg[-1])
        ref0 = dir_members_deg[-1][0]  # first value from most recent run
        aligned = np.zeros((M, T), dtype=float)
        for m in range(M):
            aligned[m, :] = align_angles_to_reference(dir_members_deg[m], ref0)

        # For each time, compute weighted quantiles over members
        qs = np.asarray(qs)
        out = np.zeros((len(qs), T), dtype=float)
        for t in range(T):
            vals = aligned[:, t]
            qrad = weighted_quantile(vals, qs, sample_weight=weights)
            out[:, t] = (np.rad2deg(qrad) + 360.0) % 360.0
        return out  # shape (len(qs), T)

    # ---------- gather files & metadata ----------
    path_dir = "data/alaro/"
    coordinates = get_city_coordinates(city)
    u_files, v_files, temp_files, precip_files, humidity_files, path_folder, initial_file = find_latest_alaro_uv_files()
    print("Path file:", initial_file)

    idx_lat, idx_lon, initial_time = basic_data_info(initial_file, coordinates, city)
    time_txt = pd.to_datetime(initial_time.values).to_pydatetime()
    ref_time = time_txt.strftime("%Y-%m-%d_%H")
    time_txt = datetime.strptime(str(time_txt)[:13], "%Y-%m-%d %H")

    # ---------- read 4 members ----------
    wind_members = []
    tprh_members = []
    for tt in range(4):
        df_wind = wind_speed_grib(u_files[tt], v_files[tt], path_folder, coordinates, city)
        df_tprh = temperature_grib(
            temp_files[tt], precip_files[tt], humidity_files[tt], path_folder, coordinates, city
        )
        wind_members.append(df_wind)
        tprh_members.append(df_tprh)

    # Align all members on the time axis of the most recent run (last one)
    base_time = wind_members[-1]["time"]
    def align_df(df, cols):
        x = df.set_index("time").reindex(base_time).interpolate(method="time").reset_index()
        x.rename(columns={"index": "time"}, inplace=True)
        return x[["time"] + cols]

    wind_members = [align_df(df, ["wind_speed", "wind_direction"]) for df in wind_members]
    tprh_members = [align_df(df, ["temperature", "hourly_rainfall", "humidity"]) for df in tprh_members]

    times = base_time.values

    # Build member matrices
    M = 4
    Tn = len(times)
    T_K = np.zeros((M, Tn))
    R_mm = np.zeros((M, Tn))
    WS = np.zeros((M, Tn))
    WD_deg = np.zeros((M, Tn))

    for m in range(M):
        T_K[m, :] = tprh_members[m]["temperature"].to_numpy()        # Kelvin
        R_mm[m, :] = (tprh_members[m]["hourly_rainfall"] * 1000.0).to_numpy()  # convert m->mm
        WS[m, :] = wind_members[m]["wind_speed"].to_numpy()
        WD_deg[m, :] = wind_members[m]["wind_direction"].to_numpy()

    # ---------- weights: last member most probable ----------
    # linear ramp: [1,2,3,4] -> normalized; feel free to tweak if you prefer geometric
    w = np.arange(1, M + 1, dtype=float)
    w /= w.sum()

    # ---------- compute weighted stats ----------
    qs_coarse = [0.10, 0.25, 0.50, 0.75, 0.90]  # 10-90 and IQR bands + median
    q10, q25, q50, q75, q90 = qs_coarse

    # scalar vars (use weighted quantiles directly)
    T_C_qs = np.zeros((5, Tn))
    R_qs   = np.zeros((5, Tn))
    WS_qs  = np.zeros((5, Tn))

    for t in range(Tn):
        T_C_qs[:, t] = weighted_quantile(T_K[:, t] - 273.15, qs_coarse, w)
        R_qs[:, t]   = weighted_quantile(R_mm[:, t],            qs_coarse, w)
        WS_qs[:, t]  = weighted_quantile(WS[:, t],              qs_coarse, w)

    # wind direction (circular)
    WD_qs = weighted_direction_quantiles([WD_deg[m, :] for m in range(M)], w, qs_coarse)
    # central tendency for direction -> the weighted "median" track
    WD_med = WD_qs[2, :]

    # also keep the most recent (last) member for overlay
    last_T = T_K[-1, :] - 273.15
    last_R = R_mm[-1, :]
    last_WS = WS[-1, :]
    last_WD = WD_deg[-1, :]

    # ---------- plotting ----------
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(f"Weather Forecast for {city.capitalize()} - {str(ref_time)}", fontsize=16, fontweight='bold')

    def plot_band(ax, x, qlo, qhi, alpha=0.20):
        ax.fill_between(x, qlo, qhi, alpha=alpha, linewidth=0, color="Tab:red")

    # Temperature
    axs[0, 0].set_title("Temperature")
    plot_band(axs[0, 0], times, T_C_qs[0], T_C_qs[4])
    #plot_band(axs[0, 0], times, T_C_qs[1], T_C_qs[3], "25–75%")
    axs[0, 0].plot(times, T_C_qs[2], linewidth=2.0, label="Weighted median")
    axs[0, 0].plot(times, last_T, linestyle="--", linewidth=1, label="Most recent run", color="Tab:green")
    axs[0, 0].set_ylim(0, 30)
    axs[0, 0].set_ylabel("Temperature [°C]")

    # Precipitation (mm/h)
    axs[1, 0].set_title("Precipitation")
    plot_band(axs[1, 0], times, R_qs[0], R_qs[4])
    #plot_band(axs[1, 0], times, R_qs[1], R_qs[3], "25–75%")
    axs[1, 0].plot(times, R_qs[2], linewidth=2.0, label="Weighted median")
    axs[1, 0].plot(times, last_R, linestyle="--", linewidth=1, label="Most recent run", color="Tab:green")
    axs[1, 0].set_ylim(-0.1, 6)
    axs[1, 0].set_ylabel("Hourly rainfall [mm]")

    # Wind speed
    axs[0, 1].set_title("Wind speed")
    plot_band(axs[0, 1], times, WS_qs[0], WS_qs[4])
    #plot_band(axs[0, 1], times, WS_qs[1], WS_qs[3], "25–75%")
    axs[0, 1].plot(times, WS_qs[2], linewidth=2.0, label="Weighted median")
    axs[0, 1].plot(times, last_WS, linestyle="--", linewidth=1, label="Most recent run", color="Tab:green")
    axs[0, 1].set_ylim(0, 12)
    axs[0, 1].set_ylabel("Wind speed [m/s]")

    # Wind direction (circular)
    axs[1, 1].set_title("Wind direction")
    # For visualization, create a band that respects wrap by plotting two copies around 0/360 if needed.
    # Here we assume 0..360 y-limits and just plot bands directly; quantiles were circularly aligned.
    def plot_dir_bands(ax, x, qarr):
        # qarr: shape (5, T): [q10,q25,q50,q75,q90]
        plot_band(ax, x, qarr[0], qarr[4])
        #plot_band(ax, x, qarr[1], qarr[3], f"{label_base} 25–75%")
        ax.plot(x, qarr[2], linewidth=2.0)

    plot_dir_bands(axs[1, 1], times, WD_qs)
    axs[1, 1].plot(times, last_WD, linestyle="--", linewidth=1, label="Most recent run", color="Tab:green")
    axs[1, 1].set_ylim(0, 360)
    axs[1, 1].set_yticks(np.arange(0, 361, 60))
    axs[1, 1].set_ylabel("Direction [°]")

    # shared x/grid/legend
    for ss in range(2):
        axs[1, ss].set_xlabel("Time")
        axs[1, ss].grid(True)
        axs[1, ss].tick_params(axis='x', rotation=30)
    for ff in range(2):
        axs[0, ff].set_xticklabels([])

    # one combined legend
    # Place a single legend below the title
    handles, labels = [], []
    for ax in axs.ravel():
        h, l = ax.get_legend_handles_labels()
        handles += h
        labels += l
    # de-duplicate labels
    uniq = dict(zip(labels, handles))
    fig.legend(uniq.values(), uniq.keys(), loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 0.94))

    filename = f'weather_forecast_{city}_{ref_time}_prob.png'
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(filename, dpi=400)
    print(f"Weather Forecast for {city.capitalize()} (probabilistic)")
    print('Saved as: ', filename)
    os.system(f"code {filename}")


#####################################################################################

def get_city_coordinates(city):

   cities_coords = {
        "antwerp": (51.2113, 4.41038),
        "spa": (51.1954, 4.3615),
        "brussels": (50.8503, 4.3517),
        "ghent": (51.0543, 3.7174),
        "bruges": (51.2093, 3.2247),
        "liege": (50.6326, 5.5797),
        "namur": (50.4674, 4.8718),
        "leuven": (50.87929, 4.7007),
        "mol": (51.2179, 5.0800),
        "mechelen": (51.0256, 4.4777),
        "hasselt": (50.9307, 5.3370),
        "genk": (50.9650, 5.5000),
        "kortrijk": (50.8262, 3.2649),
        "turnhout": (51.3226, 4.9446),
        "tournai": (50.6050, 3.3878),
        "mons": (50.4542, 3.9513),
        "charleroi": (50.4114, 4.4447),
        "aalst": (50.9360, 4.0353),
        "sint-niklaas": (51.1650, 4.1433),
        "roeselare": (50.9460, 3.1228),
        "ostend": (51.2300, 2.9126),
        "eupen": (50.6270, 6.0346),
        "berchem": (51.1876, 4.44038),
        'durnal': (50.3356, 4.99058)
    }
   
   if city not in cities_coords:
       available = ", ".join(cities_coords.keys())
       raise ValueError(f"City '{city}' not found. Available cities: {available}")
   
   city_coords = cities_coords[city]
   
   return city_coords

if __name__ == "__main__":
    main()