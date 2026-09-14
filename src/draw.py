import pathlib
import platform
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import ttu_tower.definitions as d
import windprofiles.lib.atmos as atmos

import loader
from plotting import plot_smoothed

PLOTS_DIR = pathlib.Path(__file__).resolve().parent.parent / "plots"

DATEFORMATTER = mdates.DateFormatter("%H:%M", tz="US/Central")


def _date_label(identifier):
    date = datetime.strptime(identifier[2:], "%d%b%Y")
    return date.strftime("%B %#d, %Y" if platform.system() == "Windows" else "%B %-d, %Y")


def plot_temperature_pressure(df, date_label):
    T_f = lambda T_c: T_c * 1.8 + 32.
    T_c = lambda T_f: (T_f - 32.) / 1.8
    fig, (ax_t, ax_p) = plt.subplots(figsize=(16, 10), nrows=2, sharex=True)
    ax_t.plot(df["timestamp"], df["t_4_mean"] - 273.15)
    ax_t2 = ax_t.secondary_yaxis("right", functions=(T_f, T_c))
    ax_t.xaxis.set_major_formatter(DATEFORMATTER)
    ax_t.set_ylabel("°C")
    ax_t2.set_ylabel("°F")
    ax_p.plot(df["timestamp"], atmos.pressure_to_slp(df["p_4_mean"], d.LOCATION.elevation + d.ALL_HEIGHTS_DICT[4], d.LOCATION.g) * 10)  # type: ignore
    ax_p.xaxis.set_major_formatter(DATEFORMATTER)
    ax_p.set_ylabel("hPa")
    ax_t.set_title("10m Temperature")
    ax_p.set_title("Sea Level Pressure")
    fig.suptitle(date_label)
    return fig


def plot_stability_shear(df, date_label):
    fig, ax = plt.subplots(figsize=(16, 10))
    plot_smoothed(ax, df["timestamp"], df["Rib_2-4"], window=10, method="median", label=r"Ri$_b$", color="tab:blue")
    ax.set_ylim(-0.25, 0.25)
    ax.set_ylabel(r"Ri$_b$")
    ax.plot([df["timestamp"].min(), df["timestamp"].max()], [0, 0], label=r"Ri$_b=0$", color="gray", linestyle="dashed")
    ax2 = ax.twinx()
    ax2.plot(df["timestamp"], df["alpha"], label=r"$\alpha$", color="tab:orange")
    ax2.set_ylim(0, 0.8)
    ax2.set_ylabel(r"$\alpha$")
    ax2.plot([df["timestamp"].min(), df["timestamp"].max()], [1 / 7, 1 / 7], label=r"$\alpha=1/7$", color="red", linestyle="dashed")
    ax.xaxis.set_major_formatter(DATEFORMATTER)
    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(handles1 + handles2, labels1 + labels2, loc="upper right")
    fig.suptitle(f"{date_label}\nWind shear exponent and surface stability")
    return fig


def plot_solar_precip(df, date_label):
    fig, ax = plt.subplots(figsize=(16, 10))
    solar = df.dropna(subset=["solar"])
    ax.plot(solar["timestamp"], solar["solar"], color="tab:orange", label="Solar Radiation")
    ax.set_ylabel("Solar Radiation (W/m²)")
    ax2 = ax.twinx()
    precip = df.dropna(subset=["precip"])
    ax2.bar(precip["timestamp"], precip["precip"], width=1 / 288, color="tab:blue", label="Precipitation")
    ax2.set_ylabel("Precipitation (in)")
    ax.xaxis.set_major_formatter(DATEFORMATTER)
    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(handles1 + handles2, labels1 + labels2, loc="upper right")
    fig.suptitle(f"{date_label}\nSolar radiation and precipitation")
    return fig


def plot_wind_speeds(df, date_label):
    fig, ax = plt.subplots(figsize=(16, 10))
    for b, h in d.ALL_HEIGHTS_DICT.items():
        plot_smoothed(ax, df["timestamp"], df[f"ws_{b}_mean"], window=15, method="mean", label=f"{h} m")
    ax.legend()
    ax.xaxis.set_major_formatter(DATEFORMATTER)
    fig.suptitle(f"{date_label}\nWind speeds")
    return fig


def plot_turbulence_intensity(df, date_label):
    fig, ax = plt.subplots(figsize=(16, 10))
    for b, h in d.ALL_HEIGHTS_DICT.items():
        plot_smoothed(ax, df["timestamp"], df[f"ti_{b}"], window=15, method="mean", label=f"{h} m")
    ax.legend()
    ax.xaxis.set_major_formatter(DATEFORMATTER)
    fig.suptitle(f"{date_label}\nTurbulence intensities")
    return fig


def plot_length_scale_u(df, date_label):
    fig, ax = plt.subplots(figsize=(16, 10))
    for b, h in d.ALL_HEIGHTS_DICT.items():
        plot_smoothed(ax, df["timestamp"], df[f"ILS-efolding_u_{b}"] / d.ALL_HEIGHTS_DICT[b], window=60, method="median", label=f"{h} m")
    ax.legend()
    ax.set_yscale("log")
    ax.set_ylabel(r"$L_u/Z$")
    ax.xaxis.set_major_formatter(DATEFORMATTER)
    fig.suptitle(f"{date_label}\nU length scales")
    return fig


def plot_length_scale_v(df, date_label):
    fig, ax = plt.subplots(figsize=(16, 10))
    for b, h in d.ALL_HEIGHTS_DICT.items():
        plot_smoothed(ax, df["timestamp"], df[f"ILS-efolding_v_{b}"] / d.ALL_HEIGHTS_DICT[b], window=60, method="median", label=f"{h} m")
    ax.legend()
    ax.set_yscale("log")
    ax.set_ylabel(r"$L_v/Z$")
    ax.xaxis.set_major_formatter(DATEFORMATTER)
    fig.suptitle(f"{date_label}\nV length scales")
    return fig


def plot_length_scale_w(df, date_label):
    fig, ax = plt.subplots(figsize=(16, 10))
    for b, h in d.ALL_HEIGHTS_DICT.items():
        plot_smoothed(ax, df["timestamp"], df[f"ILS-efolding_w_{b}"] / d.ALL_HEIGHTS_DICT[b], window=60, method="median", label=f"{h} m")
    ax.legend()
    ax.set_ylabel(r"$L_w/Z$")
    ax.xaxis.set_major_formatter(DATEFORMATTER)
    fig.suptitle(f"{date_label}\nW length scales")
    return fig


PLOTS = {
    "temperature_pressure": plot_temperature_pressure,
    "stability_shear": plot_stability_shear,
    "solar_precip": plot_solar_precip,
    "wind_speeds": plot_wind_speeds,
    "turbulence_intensity": plot_turbulence_intensity,
    "length_scale_u": plot_length_scale_u,
    "length_scale_v": plot_length_scale_v,
    "length_scale_w": plot_length_scale_w,
}


def draw_all(identifier):
    df = loader.load(identifier)
    date_label = _date_label(identifier)
    out_dir = PLOTS_DIR / identifier
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, plot_fn in PLOTS.items():
        fig = plot_fn(df, date_label)
        fig.savefig(out_dir / f"{name}.png", dpi=150)
        plt.close(fig)


def main():
    for identifier in loader.available_data():
        print(f"Drawing plots for {identifier}")
        draw_all(identifier)


if __name__ == "__main__":
    main()
