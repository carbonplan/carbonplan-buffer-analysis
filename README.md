<p align="left" >
<a href='https://carbonplan.org'>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://carbonplan-assets.s3.amazonaws.com/monogram/light-small.png">
  <img alt="CarbonPlan monogram." height="48" src="https://carbonplan-assets.s3.amazonaws.com/monogram/dark-small.png">
</picture>
</a>
</p>

# carbonplan-buffer-analysis

An analysis of California's forest offsets program that compares the program's buffer pool against estimates of carbon loss due to wildfire and the pathogen, _Phytophthora ramorum_.

[![CI](https://github.com/carbonplan/carbonplan-buffer-analysis/actions/workflows/main.yaml/badge.svg)](https://github.com/carbonplan/carbonplan-buffer-analysis/actions/workflows/main.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## usage

This codebase primarily consists of a series of `prefect` workflows that load, subset, and aggreate input datasets.

The `notebooks` folder contains two annotated descriptions of how we calculated project pre-fire biomass, as well as project wood product salvage fractions.
Two additional notebooks generate figures that support our analysis.

The `analysis` folder contains the code to generate figures.

## data sources
All data are available in a [public cloud storage bucket](https://console.cloud.google.com/storage/browser/carbonplan-buffer-analysis).
We've also archived [a copy of the inputs and outputs of the analysis](TK) to Zenodo.

## license

All the code in this repository is [MIT](https://choosealicense.com/licenses/mit/)-licensed, but we request that you please provide attribution if reusing any of our digital content (graphics, logo, articles, etc.).

## about us

CarbonPlan is a nonprofit organization that uses data and science for climate action. We aim to improve the transparency and scientific integrity of climate solutions with open data and tools. Find out more at [carbonplan.org](https://carbonplan.org/) or get in touch by [opening an issue](https://github.com/carbonplan/carbonplan-buffer-analysis/issues/new) or [sending us an email](mailto:hello@carbonplan.org).
