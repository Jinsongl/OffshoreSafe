"""Create a backend-independent UQRA random-variable definition."""

from uqra import RandomVariable

elastic_modulus = RandomVariable(
    name="E",
    distribution="Normal",
    parameters={"mean": 210e9, "std": 10e9},
    unit="Pa",
    description="Elastic modulus",
)

print(elastic_modulus)
