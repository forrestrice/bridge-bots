# bridge-bots
Data processing and Machine Learning for Contract Bridge

## Bridgebots Core
The most developed component of bridge-bots is the core library for parsing and representing bridge data. This is a dependency of almost all other projects in this repository. See the [Readme](bridgebots/README.md) for more details.

## Parse
Scripts for parsing specific datasets. Data is converted to a Bridgebots representation or to a common data type like CSV or JSON.

## Scrape
A basic ACBL API client (unfortunately the API documenation and registration seems to have disappeared from the ACBL website).

Web scrapers used to download data from my club's website and from BBO.

## Tools
Tools which build on the core module to process data. See the [Readme](tools/README.md).

## Train
Initial foray into creating training data for Machine Learning projects.

## Sequence
Training sequence based models to predict bidding and cardplay.
