# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def plot(
    data: pd.DataFrame,
    plot_type: str = "scatter",
    x: str = "",
    y: str = "",
    xlabel: str = "",
    ylabel: str = "",
):
    if plot_type == "scatter":
        plt.scatter(data[x], data[y])
    elif plot_type == "box":
        data[[x, y]].boxplot()
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.show()
