
# Agriculture Sector
 The agriculture sector is currently a low resolution sector which acts like a black box to ensure that agricultural energy demands are in the model. Data obtained from the NRCan Comprehensive energy use database.
        
##Commodity
| name       | description                                      | type               | units   |
|:-----------|:-------------------------------------------------|:-------------------|:--------|
| A\_ng      | Natural gas for the agriculture sector           | annual commodity   | nan     |
| A\_prop    | Represents propane in the agriculture sector     | annual commodity   | nan     |
| A\_dsl     | Represents Diesel in the agriculture sector      | annual commodity   | nan     |
| A\_gsl     | Represents Gasoline in the agriculture sector    | annual commodity   | nan     |
| A\_d\_agri | Demand for the Agriculture sector                | demand commodity   | PJ      |
| A\_elc     | Represents Electricity in the agriculture sector | physical commodity | nan     |

## Technology

| tech       | description                                                     |   unlim_cap |   annual |   reserve |   curtail |   flex |
|:-----------|:----------------------------------------------------------------|------------:|---------:|----------:|----------:|-------:|
| A\_AGRI    | Generic technology representing Agriculture                     |           1 |        1 |         0 |         0 |      0 |
| F\_A\_NG   | Natural gas distribution from fuel sector to agriculture sector |           1 |        1 |         0 |         0 |      0 |
| E\_A\_ELC  | Electricity distribution to agriculture sector                  |           1 |        0 |         0 |         0 |      0 |
| F\_A\_DSL  | Diesel distribution from fuel sector to agriculture sector      |           1 |        1 |         0 |         0 |      0 |
| F\_A\_PROP | Propane distribution from fuel sector to agriculture sector     |           1 |        1 |         0 |         0 |      0 |
| F\_A\_GSL  | Gasoline distribution from fuel sector to agriculture sector    |           1 |        1 |         0 |         0 |      0 |
