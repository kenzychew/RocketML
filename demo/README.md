---
title: RocketML Sentiment Demo
colorFrom: yellow
colorTo: red
sdk: gradio
sdk_version: 5.50.0
app_file: main.py
python_version: "3.12"
short_description: TF-IDF + LogReg sentiment classifier (RocketML demo)
---

# RocketML -- sentiment demo

A live demo of the model served by [RocketML](https://github.com/kenzychew/RocketML):
a TF-IDF + LogisticRegression sentiment classifier trained on IMDB reviews. Type a
movie review and get a positive/negative label with a confidence score.

The point of RocketML is the platform around the model -- containerised serving,
CI to GHCR, Prometheus/Grafana monitoring, and a Helm chart for Kubernetes. This
Space is just the model on its own so you can try it.
