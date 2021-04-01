# GrafEner

Plotting EnergyPlus data made easy

## Setup

### Using docker

Build docker image:

```shell
docker build -t grafener -f docker/Dockerfile .
```

### Using docker-compose

Build the image:

```shell
docker-compose -f ./docker/docker-compose.yml build grafener
```

Docker compose configuration provided here brings several benefits:
- GrafEner configuration is persisted (not lost when container is stopped)
- docker configuration is centralized in a file (see `docker/docker-compose.yml`)  
- datasources are automatically provisioned (see `docker/provisioning` to configure yours)

## Run

### Using docker

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

### Using docker-compose

```shell
docker-compose -f ./docker/docker-compose.yml up
```

## Use

### Basic usage

**Run an EnergyPlus experiment using CSV output.**

Example: 

```shell
energyplus -r -x -d /tmp/energyplus -w /path/to/weather.epw /path/to/model.idf
```

**Configure a new Simple JSON DataSource**

Open your browser at http://localhost:3000 to configure your first datasource (note: default user is `admin`, same for password).

Example: ![datasource configuration](images/ds_config.png?raw=true "Datasource configuration")

Notes:
- URL must be `http://localhost:8900`
- Add a `source` HTTP header that will point to `eplusout.csv` file. In present example, it will be at 
  `/tmp/eplus_data/eplusout.csv`

**Enjoy!**

Create a new dashboard, add a panel and start browsing EnergyPlus data. All CSV columns are now Grafana metrics 

![transform](images/transform.png?raw=true "Transformation")

### Using multiple sources

It can be useful to compare results of different EnergyPlus simulations. To visualize more than one simulation output:

**Configure more than 1 datasource**

Using a friendly but unique identifer in URL path. For instance, if you have 2 sources:

- Datasource 1 URL: `http://localhost:8900/myXp1`
- Datasource 2 URL: `http://localhost:8900/myXp2`

**Use -- Mixed -- datasource type**

In a new panel, use the *-- Mixed --* datasource type, then start adding metrics: Grafana will ask you to provide the 
datasource first, so you can choose between myXp1 and myXp2

**Visualize and compare**

In this mode, metric names have their respective datasource name as a prefix. It allows to identify them, and apply 
post-processing (like _series overriding_)

Example:

![mixed](images/mixed.png?raw=true "Mixed DS")

## Roadmap

- add support for remote sources (http, s3, ...)
- cache large data frames on disk rather than memory
- use `pyenergyplus` Python bindings to start EnergyPlus simulation and plot live
- add support for annotations
