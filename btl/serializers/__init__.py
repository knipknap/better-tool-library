from .camoticsserializer import CamoticsSerializer
from .fcserializer import FCSerializer
from .linuxcncserializer import LinuxCNCSerializer

serializers = {
    'camotics': CamoticsSerializer,
    'freecad': FCSerializer,
    'linuxcnc': LinuxCNCSerializer,
}
