import pandas as pd


def plot_smoothed(ax, x, y, window, method="mean", **kwargs):
    rolling = pd.Series(y).rolling(window, center=True)
    if method == "mean":
        smoothed = rolling.mean()
    elif method == "median":
        smoothed = rolling.median()
    else:
        raise ValueError(f"Unknown method '{method}', expected 'mean' or 'median'")
    return ax.plot(x, smoothed, **kwargs)
