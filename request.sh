#!/bin/bash


http get https://api.etherscan.io/api \
   ?module=stats \
   &action=tokensupply\
   &contractaddress=QWC99R35T4QMK5VX17NBWBTA2B5NAFH499\
   &apikey=YourApiKeyToken