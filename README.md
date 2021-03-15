# Grafener

Plotting EnergyPlus data made easy

## Setup

Build docker image:

```shell
docker build -t grafener -f docker/Dockerfile .
```

## Run

```shell
docker run --rm \
  -p 3000:3000 \
  --env "SIM_YEAR=2020" \
  -v /path/to/energyplus/output/folder/:/tmp/eplus_data:ro \
  --name grafener \
  grafener
```

With:

- `--env "SIM_YEAR=2020"` allows to pin simulation year (not provided by default in `Date/Time` column of EnergyPlus CSV
  output). Default is current year.
- `-v /tmp/energyplus:/tmp/eplus_data:ro` mounts a directory where EnergyPlus csv output is located (
  typically `eplusout.csv`) with read-only permission. Data will be available inside the container at `/tmp/eplus_data`

## Use

1. Run an EnergyPlus experiment using CSV output. Example: `energyplus -r -x -d /tmp/energyplus -w /path/to/weather.epw /path/to/model.idf`
2. Open you browser at http://localhost:3000
3. Configure a new Simple JSON DataSource as following:
   1. URL must be `http://localhost:8900`
   2. Add a `source` HTTP header that will point to `eplusout.csv` file. In present example, it will be at `/tmp/eplus_data/eplusout.csv`
    Example: ![datasource configuration](images/ds_config.png?raw=true "Datasource configuration")
4. Enjoy! Create a new dashboard, add a panel and start browsing EnergyPlus data   