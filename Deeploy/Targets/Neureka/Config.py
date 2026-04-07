from dataclasses import dataclass

@dataclass
class NeurekaConfig:
    weight_bandwidth_1x1:  int = 256
    weight_bandwidth_3x3:  int = 256
    cin_subtile_1x1:   int = 32
    cin_subtile_3x3:   int = 28
    # room for other HW params

_DEFAULT_NEUREKA_CONFIG = NeurekaConfig()