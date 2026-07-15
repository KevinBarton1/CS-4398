from .traffic_simulator import heatmap_grid


def build_heatmap(congestion, demand, hour, mode):
    allowed = {"congestion", "demand", "profitability", "off"}
    if mode not in allowed:
        mode = "congestion"
    return {"mode": mode, "cells": [] if mode == "off" else heatmap_grid(congestion, demand, hour, mode)}

