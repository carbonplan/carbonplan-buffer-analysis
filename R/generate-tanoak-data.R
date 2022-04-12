library(rFIA)
data <- readFIA(states = ‘CA’, dir=‘/Users/darryl/Desktop/raw_fia/’, common=TRUE, nCores=2)
recent <- clipFIA(data, mostRecent = TRUE)

plot_species_biomass <- biomass(data, byPlot = TRUE, bySpecies = TRUE)
plot_biomass <- biomass(data, byPlot = TRUE)
plot_species_tpa <- tpa(data, byPlot = TRUE, bySpecies = TRUE)
plot_tpa <- tpa(data, byPlot = TRUE)

# results manually uploaded to gcs
